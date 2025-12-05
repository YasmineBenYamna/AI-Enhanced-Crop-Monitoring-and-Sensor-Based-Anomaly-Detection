"""
ML Module - Django Views
API endpoints for anomaly detection.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist

from .anomaly_detector import IsolationForestDetector, AnomalyDetectionService
from .preprocessing import preprocess_sensor_data, get_recent_readings
from crop_app.models import SensorReading, AnomalyEvent
from datetime import datetime
import numpy as np


# Global detector instance (in production, use caching or database)
_detector_cache = {}


def get_or_create_detector(sensor_type: str) -> IsolationForestDetector:
    """
    Get cached detector or create new one.
    
    Args:
        sensor_type: Sensor type (moisture, temperature, humidity)
    
    Returns:
        IsolationForestDetector instance
    """
    if sensor_type not in _detector_cache:
        _detector_cache[sensor_type] = IsolationForestDetector(contamination=0.1)
    
    return _detector_cache[sensor_type]


@api_view(['POST'])
def train_model(request):
    """
    Train the anomaly detection model on normal data.
    
    POST /api/ml/train/
    Body:
    {
        "sensor_type": "moisture",
        "plot_id": 1,
        "use_recent_data": true,  // Use data from database
        "data_points": 100  // Number of recent readings to use
    }
    
    Or provide custom training data:
    {
        "sensor_type": "moisture",
        "training_data": [[60, 2, 55, 65, 10], [58, 3, 50, 63, 13], ...]
    }
    """
    sensor_type = request.data.get('sensor_type')
    
    if not sensor_type:
        return Response(
            {'error': 'sensor_type required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        detector = get_or_create_detector(sensor_type)
        
        # Option 1: Use recent database data
        if request.data.get('use_recent_data'):
            plot_id = request.data.get('plot_id', 1)
            data_points = request.data.get('data_points', 100)
            
            # Get recent normal readings
            values = get_recent_readings(plot_id, sensor_type, count=data_points)
            
            if len(values) < 10:
                return Response(
                    {'error': f'Not enough data. Need 10+, have {len(values)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Preprocess
            from .preprocessing import SensorDataPreprocessor
            preprocessor = SensorDataPreprocessor(window_size=10)
            training_data = preprocessor.prepare_for_model(values, use_features=True)
        
        # Option 2: Use provided training data
        elif 'training_data' in request.data:
            training_data = np.array(request.data['training_data'])
        
        else:
            return Response(
                {'error': 'Either use_recent_data or training_data required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Train the model
        stats = detector.train(training_data)
        
        return Response({
            'success': True,
            'message': f'Model trained for {sensor_type}',
            'stats': stats
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def detect_anomalies(request):
    """
    Detect anomalies in sensor data.
    
    POST /api/ml/detect/
    Body:
    {
        "plot_id": 1,
        "sensor_type": "moisture"
    }
    """
    plot_id = request.data.get('plot_id')
    sensor_type = request.data.get('sensor_type')
    
    if not plot_id or not sensor_type:
        return Response(
            {'error': 'plot_id and sensor_type required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        detector = get_or_create_detector(sensor_type)
        
        if not detector.is_trained:
            return Response(
                {'error': f'Model for {sensor_type} not trained yet. Call /api/ml/train/ first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get recent readings
        values = get_recent_readings(plot_id, sensor_type, count=50)
        
        if len(values) < 10:
            return Response(
                {'error': f'Not enough data. Need 10+, have {len(values)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Preprocess
        from .preprocessing import SensorDataPreprocessor
        preprocessor = SensorDataPreprocessor(window_size=10)
        processed_data = preprocessor.prepare_for_model(values, use_features=True)
        
        # Detect anomalies
        results = detector.detect_with_confidence(processed_data)
        
        # Filter to show only anomalies
        anomalies = [r for r in results if r['is_anomaly']]
        
        # Create AnomalyEvent records for detected anomalies
        created_events = []
        for anomaly in anomalies:
            event = AnomalyEvent.objects.create(
                plot_id=plot_id,
                sensor_type=sensor_type,
                anomaly_type='sensor_anomaly',
                severity=anomaly['severity'],
                model_confidence=anomaly['confidence'],
                timestamp=datetime.now()
            )
            created_events.append(event.id)
        
        return Response({
            'success': True,
            'plot_id': plot_id,
            'sensor_type': sensor_type,
            'total_windows': len(results),
            'anomalies_detected': len(anomalies),
            'anomaly_events_created': created_events,
            'results': results
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def model_status(request):
    """
    Get status of trained models.
    
    GET /api/ml/status/
    """
    status_info = {}
    
    for sensor_type in ['moisture', 'temperature', 'humidity']:
        if sensor_type in _detector_cache:
            detector = _detector_cache[sensor_type]
            status_info[sensor_type] = {
                'trained': detector.is_trained,
                'training_data_size': detector.training_data_size,
                'training_date': detector.training_date.isoformat() if detector.training_date else None
            }
        else:
            status_info[sensor_type] = {
                'trained': False,
                'training_data_size': 0,
                'training_date': None
            }
    
    return Response(status_info, status=status.HTTP_200_OK)


@api_view(['POST'])
def batch_detect(request):
    """
    Run anomaly detection on all plots and sensors.
    
    POST /api/ml/batch-detect/
    Body:
    {
        "plot_ids": [1, 2, 3],  // Optional, default: all plots
        "sensor_types": ["moisture", "temperature"]  // Optional, default: all sensors
    }
    """
    plot_ids = request.data.get('plot_ids')
    sensor_types = request.data.get('sensor_types', ['moisture', 'temperature', 'humidity'])
    
    # Get all plot IDs if not specified
    if not plot_ids:
        from crop_app.models import FieldPlot
        plot_ids = list(FieldPlot.objects.values_list('id', flat=True))
    
    results = []
    
    for plot_id in plot_ids:
        for sensor_type in sensor_types:
            try:
                detector = get_or_create_detector(sensor_type)
                
                if not detector.is_trained:
                    results.append({
                        'plot_id': plot_id,
                        'sensor_type': sensor_type,
                        'status': 'skipped',
                        'reason': 'model not trained'
                    })
                    continue
                
                # Get and process data
                values = get_recent_readings(plot_id, sensor_type, count=50)
                
                if len(values) < 10:
                    results.append({
                        'plot_id': plot_id,
                        'sensor_type': sensor_type,
                        'status': 'skipped',
                        'reason': 'insufficient data'
                    })
                    continue
                
                # Preprocess and detect
                from .preprocessing import SensorDataPreprocessor
                preprocessor = SensorDataPreprocessor(window_size=10)
                processed_data = preprocessor.prepare_for_model(values, use_features=True)
                
                detections = detector.detect_with_confidence(processed_data)
                anomalies = [d for d in detections if d['is_anomaly']]
                
                # Create events
                for anomaly in anomalies:
                    AnomalyEvent.objects.create(
                        plot_id=plot_id,
                        sensor_type=sensor_type,
                        anomaly_type='sensor_anomaly',
                        severity=anomaly['severity'],
                        model_confidence=anomaly['confidence'],
                        timestamp=datetime.now()
                    )
                
                results.append({
                    'plot_id': plot_id,
                    'sensor_type': sensor_type,
                    'status': 'success',
                    'anomalies_detected': len(anomalies)
                })
            
            except Exception as e:
                results.append({
                    'plot_id': plot_id,
                    'sensor_type': sensor_type,
                    'status': 'error',
                    'error': str(e)
                })
    
    return Response({
        'success': True,
        'results': results,
        'total_processed': len(results),
        'total_anomalies': sum(r.get('anomalies_detected', 0) for r in results)
    }, status=status.HTTP_200_OK)