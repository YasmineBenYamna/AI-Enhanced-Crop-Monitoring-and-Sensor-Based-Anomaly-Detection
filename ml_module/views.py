"""
ML Module - Django Views
API endpoints for anomaly detection.
Models are saved to disk for persistence.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from .anomaly_detector import IsolationForestDetector
from .preprocessing import get_recent_readings
from crop_app.models import SensorReading, AnomalyEvent
from datetime import datetime
import numpy as np
import os


# Directory to store trained models
MODEL_DIR = os.path.join(settings.BASE_DIR, 'trained_models')

# Create directory if it doesn't exist
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

# Global detector cache (loaded from disk on first use)
_detector_cache = {}


def get_model_path(sensor_type: str) -> str:
    """Get file path for a sensor type's model."""
    return os.path.join(MODEL_DIR, f'{sensor_type}_model.pkl')


def get_or_create_detector(sensor_type: str) -> IsolationForestDetector:
    """
    Get cached detector or load from disk.
    
    Args:
        sensor_type: Sensor type (moisture, temperature, humidity)
    
    Returns:
        IsolationForestDetector instance
    """
    # Check RAM cache first
    if sensor_type in _detector_cache:
        return _detector_cache[sensor_type]
    
    # Try to load from disk
    model_path = get_model_path(sensor_type)
    
    if os.path.exists(model_path):
        try:
            # Load from disk
            detector = IsolationForestDetector.load_model(model_path)
            _detector_cache[sensor_type] = detector
            print(f"✅ Loaded {sensor_type} model from disk")
            return detector
        except Exception as e:
            print(f"⚠️ Failed to load {sensor_type} model from disk: {e}")
    
    # Create new detector if not found
    detector = IsolationForestDetector(contamination=0.1)
    _detector_cache[sensor_type] = detector
    return detector


@api_view(['POST'])
@permission_classes([AllowAny])
def train_model(request):
    """
    Train the anomaly detection model on normal data.
    Model is saved to disk after training.
    
    POST /api/ml/train/
    Body:
    {
        "sensor_type": "moisture",
        "plot_id": 1,
        "use_recent_data": true,
        "data_points": 100
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
        
        # SAVE TO DISK ⭐
        model_path = get_model_path(sensor_type)
        detector.save_model(model_path)
        print(f"💾 Saved {sensor_type} model to {model_path}")
        
        return Response({
            'success': True,
            'message': f'Model trained and saved for {sensor_type}',
            'model_path': model_path,
            'stats': stats
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
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
                anomaly_type=f'{sensor_type}_anomaly',
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
@permission_classes([AllowAny])
def model_status(request):
    """
    Get status of trained models (from disk and RAM).
    
    GET /api/ml/status/
    """
    status_info = {}
    
    for sensor_type in ['moisture', 'temperature', 'humidity']:
        # Check if model exists on disk
        model_path = get_model_path(sensor_type)
        model_exists_on_disk = os.path.exists(model_path)
        
        # Get detector (loads from disk if available)
        detector = get_or_create_detector(sensor_type)
        
        status_info[sensor_type] = {
            'trained': detector.is_trained,
            'training_data_size': detector.training_data_size,
            'training_date': detector.training_date.isoformat() if detector.training_date else None,
            'saved_to_disk': model_exists_on_disk,
            'model_path': model_path if model_exists_on_disk else None
        }
    
    return Response(status_info, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def batch_detect(request):
    """
    Run anomaly detection on all plots and sensors.
    
    POST /api/ml/batch-detect/
    Body:
    {
        "plot_ids": [1, 2, 3],
        "sensor_types": ["moisture", "temperature"]
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
                        anomaly_type=f'{sensor_type}_anomaly',
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