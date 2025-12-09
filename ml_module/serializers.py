"""
ML Module - Serializers
Serializers for ViewSet-based ML API endpoints.
"""

from rest_framework import serializers
from crop_app.models import AnomalyEvent


# ============================================================================
# INPUT SERIALIZERS (Request Validation)
# ============================================================================

class TrainModelSerializer(serializers.Serializer):
    """Validate input for model training."""
    
    sensor_type = serializers.ChoiceField(
        choices=['moisture', 'temperature', 'humidity'],
        required=True,
        help_text="Type of sensor to train model for"
    )
    
    plot_id = serializers.IntegerField(
        required=False,
        default=1,
        help_text="Plot ID to use for training data"
    )
    
    use_recent_data = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Use recent data from database for training"
    )
    
    data_points = serializers.IntegerField(
        required=False,
        default=100,
        min_value=10,
        max_value=1000,
        help_text="Number of recent readings to use"
    )
    
    training_data = serializers.ListField(
        child=serializers.ListField(
            child=serializers.FloatField()
        ),
        required=False,
        allow_null=True,
        help_text="Custom training data (array of feature arrays)"
    )
    
    def validate(self, data):
        """Ensure either use_recent_data or training_data is provided."""
        if not data.get('use_recent_data') and not data.get('training_data'):
            raise serializers.ValidationError(
                "Either use_recent_data or training_data must be provided"
            )
        return data


class DetectAnomaliesSerializer(serializers.Serializer):
    """Validate input for anomaly detection."""
    
    plot_id = serializers.IntegerField(
        required=True,
        help_text="Plot ID to detect anomalies for"
    )
    
    sensor_type = serializers.ChoiceField(
        choices=['moisture', 'temperature', 'humidity'],
        required=True,
        help_text="Type of sensor to check for anomalies"
    )


class BatchDetectSerializer(serializers.Serializer):
    """Validate input for batch anomaly detection."""
    
    plot_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        allow_null=True,
        help_text="List of plot IDs (empty/null = all plots)"
    )
    
    sensor_types = serializers.ListField(
        child=serializers.ChoiceField(
            choices=['moisture', 'temperature', 'humidity']
        ),
        required=False,
        default=['moisture', 'temperature', 'humidity'],
        help_text="List of sensor types to check"
    )


# ============================================================================
# OUTPUT SERIALIZERS (Response Formatting)
# ============================================================================

class TrainingStatsSerializer(serializers.Serializer):
    """Format training statistics."""
    
    trained = serializers.BooleanField()
    n_samples = serializers.IntegerField()
    n_features = serializers.IntegerField()
    training_date = serializers.DateTimeField()
    mean_score = serializers.FloatField()


class TrainModelResponseSerializer(serializers.Serializer):
    """Format model training response."""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    stats = TrainingStatsSerializer()


class AnomalyWindowSerializer(serializers.Serializer):
    """Format individual anomaly detection window result."""
    
    index = serializers.IntegerField()
    is_anomaly = serializers.BooleanField()
    anomaly_score = serializers.FloatField()
    confidence = serializers.FloatField()
    severity = serializers.CharField()


class DetectAnomaliesResponseSerializer(serializers.Serializer):
    """Format anomaly detection response."""
    
    success = serializers.BooleanField()
    plot_id = serializers.IntegerField()
    sensor_type = serializers.CharField()
    total_windows = serializers.IntegerField()
    anomalies_detected = serializers.IntegerField()
    anomaly_events_created = serializers.ListField(
        child=serializers.IntegerField()
    )
    results = AnomalyWindowSerializer(many=True)


class BatchDetectResultSerializer(serializers.Serializer):
    """Format individual batch detection result."""
    
    plot_id = serializers.IntegerField()
    sensor_type = serializers.CharField()
    status = serializers.ChoiceField(
        choices=['success', 'skipped', 'error']
    )
    anomalies_detected = serializers.IntegerField(required=False)
    reason = serializers.CharField(required=False)
    error = serializers.CharField(required=False)


class BatchDetectResponseSerializer(serializers.Serializer):
    """Format batch detection response."""
    
    success = serializers.BooleanField()
    results = BatchDetectResultSerializer(many=True)
    total_processed = serializers.IntegerField()
    total_anomalies = serializers.IntegerField()


class ModelStatusSerializer(serializers.Serializer):
    """Format model status for one sensor type."""
    
    trained = serializers.BooleanField()
    training_data_size = serializers.IntegerField()
    training_date = serializers.DateTimeField(allow_null=True)
    saved_to_disk = serializers.BooleanField(required=False)
    model_path = serializers.CharField(required=False, allow_null=True)