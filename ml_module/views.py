"""
ML Module - ViewSets (FIXED)
API endpoints for anomaly detection using ViewSets.
All endpoints allow unauthenticated access (AllowAny).
Models are saved to disk for persistence.

FIXES:
- Uses plot=plot_object instead of plot_id=integer
- Links sensor_reading to anomaly events
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from .serializers import (
    TrainModelSerializer,
    TrainModelResponseSerializer,
    DetectAnomaliesSerializer,
    DetectAnomaliesResponseSerializer,
    BatchDetectSerializer,
    BatchDetectResponseSerializer,
    ModelStatusSerializer
)
from .anomaly_detector import IsolationForestDetector
from .preprocessing import get_recent_readings
from crop_app.models import SensorReading, AnomalyEvent, FieldPlot
from datetime import datetime
import numpy as np
import os


# ============================================================================
# MODEL MANAGEMENT
# ============================================================================

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


# ============================================================================
# VIEWSET
# ============================================================================

class MLViewSet(viewsets.ViewSet):
    """
    ViewSet for ML anomaly detection operations.
    
    Provides endpoints for:
    - train: Train anomaly detection models
    - detect: Detect anomalies for a single plot/sensor
    - batch_detect: Detect anomalies across multiple plots/sensors
    - status: Get status of trained models
    """
    
    permission_classes = [AllowAny]
    
    
    @action(detail=False, methods=['post'], url_path='train')
    def train(self, request):
        """
        Train the anomaly detection model on normal data.
        
        POST /api/ml/train/
        Body:
        {
            "sensor_type": "moisture",
            "plot_id": 1,
            "use_recent_data": true,
            "data_points": 100
        }
        """
        # Validate input
        serializer = TrainModelSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        sensor_type = serializer.validated_data['sensor_type']
        
        try:
            detector = get_or_create_detector(sensor_type)
            
            # Option 1: Use recent database data
            if serializer.validated_data.get('use_recent_data'):
                plot_id = serializer.validated_data.get('plot_id', 1)
                data_points = serializer.validated_data.get('data_points', 100)
                
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
            elif serializer.validated_data.get('training_data'):
                training_data = np.array(serializer.validated_data['training_data'])
            
            else:
                return Response(
                    {'error': 'Either use_recent_data or training_data required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Train the model
            stats = detector.train(training_data)
            
            # Save to disk
            model_path = get_model_path(sensor_type)
            detector.save_model(model_path)
            print(f"💾 Saved {sensor_type} model to {model_path}")
            
            # Format response
            response_data = {
                'success': True,
                'message': f'Model trained for {sensor_type}',
                'stats': stats
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    @action(detail=False, methods=['post'], url_path='detect')
    def detect(self, request):
        """
        Detect anomalies in sensor data.
        
        POST /api/ml/detect/
        Body:
        {
            "plot_id": 1,
            "sensor_type": "moisture"
        }
        """
        # Validate input
        serializer = DetectAnomaliesSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        plot_id = serializer.validated_data['plot_id']
        sensor_type = serializer.validated_data['sensor_type']
        
        try:
            detector = get_or_create_detector(sensor_type)
            
            if not detector.is_trained:
                return Response(
                    {'error': f'Model for {sensor_type} not trained yet. Call /api/ml/train/ first'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ✅ FIX 1: Get the FieldPlot object (not just the ID)
            try:
                plot = FieldPlot.objects.get(id=plot_id)
            except FieldPlot.DoesNotExist:
                return Response(
                    {'error': f'Plot {plot_id} does not exist'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get recent readings WITH objects (not just values)
            readings_qs = SensorReading.objects.filter(
                plot=plot,
                sensor_type=sensor_type
            ).order_by('-timestamp')[:50]
            
            readings_list = list(readings_qs)
            values = [r.value for r in readings_list]
            
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
            
            # ✅ FIX 2: Create AnomalyEvent records with proper ForeignKeys
            created_events = []
            for i, anomaly in enumerate(anomalies):
                # Get the sensor reading that corresponds to this window
                window_index = anomaly.get('index', i)
                
                # Get the most recent reading in this window (first reading of the window)
                if window_index < len(readings_list):
                    sensor_reading = readings_list[window_index]
                else:
                    sensor_reading = readings_list[0]  # Fallback to most recent
                
                # Map severity to model choices
                severity_map = {
                    'NORMAL': 'low',
                    'MINOR': 'low',
                    'WARNING': 'medium',
                    'CRITICAL': 'high'
                }
                severity = severity_map.get(anomaly['severity'], 'medium')
                
                # ✅ CORRECT: Use plot=plot_object and sensor_reading=reading_object
                event = AnomalyEvent.objects.create(
                    plot=plot,  # ← ForeignKey to FieldPlot object
                    sensor_reading=sensor_reading,  # ← ForeignKey to SensorReading object
                    anomaly_type=f'{sensor_type}_anomaly',
                    severity=severity,
                    model_confidence=anomaly['confidence']
                )
                created_events.append(event.id)
            
            response_data = {
                'success': True,
                'plot_id': plot_id,
                'sensor_type': sensor_type,
                'total_windows': len(results),
                'anomalies_detected': len(anomalies),
                'anomaly_events_created': created_events,
                'results': results
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    @action(detail=False, methods=['post'], url_path='batch-detect')
    def batch_detect(self, request):
        """
        Run anomaly detection on all plots and sensors.
        
        POST /api/ml/batch-detect/
        Body:
        {
            "plot_ids": [1, 2, 3],
            "sensor_types": ["moisture", "temperature"]
        }
        """
        # Validate input
        serializer = BatchDetectSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        plot_ids = serializer.validated_data.get('plot_ids')
        sensor_types = serializer.validated_data.get('sensor_types', ['moisture', 'temperature', 'humidity'])
        
        # Get all plot IDs if not specified
        if not plot_ids:
            plot_ids = list(FieldPlot.objects.values_list('id', flat=True))
        
        results = []
        
        for plot_id in plot_ids:
            # ✅ FIX: Get the FieldPlot object
            try:
                plot = FieldPlot.objects.get(id=plot_id)
            except FieldPlot.DoesNotExist:
                results.append({
                    'plot_id': plot_id,
                    'sensor_type': 'all',
                    'status': 'error',
                    'error': f'Plot {plot_id} does not exist'
                })
                continue
            
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
                    
                    # Get and process data WITH objects
                    readings_qs = SensorReading.objects.filter(
                        plot=plot,
                        sensor_type=sensor_type
                    ).order_by('-timestamp')[:50]
                    
                    readings_list = list(readings_qs)
                    values = [r.value for r in readings_list]
                    
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
                    
                    # ✅ FIX: Create events with proper ForeignKeys
                    for i, anomaly in enumerate(anomalies):
                        # Get corresponding sensor reading
                        window_index = anomaly.get('index', i)
                        if window_index < len(readings_list):
                            sensor_reading = readings_list[window_index]
                        else:
                            sensor_reading = readings_list[0]
                        
                        # Map severity
                        severity_map = {
                            'NORMAL': 'low',
                            'MINOR': 'low',
                            'WARNING': 'medium',
                            'CRITICAL': 'high'
                        }
                        severity = severity_map.get(anomaly['severity'], 'medium')
                        
                        # ✅ CORRECT: Use ForeignKey objects
                        AnomalyEvent.objects.create(
                            plot=plot,
                            sensor_reading=sensor_reading,
                            anomaly_type=f'{sensor_type}_anomaly',
                            severity=severity,
                            model_confidence=anomaly['confidence']
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
        
        response_data = {
            'success': True,
            'results': results,
            'total_processed': len(results),
            'total_anomalies': sum(r.get('anomalies_detected', 0) for r in results)
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    
    @action(detail=False, methods=['get'], url_path='status')
    def get_status(self, request):
        """
        Get status of trained models.
        
        GET /api/ml/status/
        """
        status_info = {}
        
        for sensor_type in ['moisture', 'temperature', 'humidity']:
            detector = get_or_create_detector(sensor_type)
            model_path = get_model_path(sensor_type)
            model_exists_on_disk = os.path.exists(model_path)
            
            status_info[sensor_type] = {
                'trained': detector.is_trained,
                'training_data_size': detector.training_data_size,
                'training_date': detector.training_date.isoformat() if detector.training_date else None,
                'saved_to_disk': model_exists_on_disk,
                'model_path': model_path if model_exists_on_disk else None
            }
        
        return Response(status_info, status=status.HTTP_200_OK)