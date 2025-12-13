"""
AI Agent - DRF Serializers
Serializers for API responses.
"""

from rest_framework import serializers
from crop_app.models import AgentRecommendation, AnomalyEvent, FieldPlot


class AnomalyEventSerializer(serializers.ModelSerializer):
    """Serializer for AnomalyEvent (nested in recommendations)."""
    
    class Meta:
        model = AnomalyEvent
        fields = [
            'id',
            'timestamp',
            'anomaly_type',
            'severity',
            'model_confidence'
        ]


class PlotSerializer(serializers.ModelSerializer):
    """Serializer for FieldPlot (nested in recommendations)."""
    
    class Meta:
        model = FieldPlot
        fields = [
            'id',
            'crop_variety',
            'plot_name'
        ]


class AgentRecommendationSerializer(serializers.ModelSerializer):
    """Main serializer for AgentRecommendation."""
    
    anomaly = AnomalyEventSerializer(source='anomaly_event', read_only=True)
    plot = PlotSerializer(source='anomaly_event.plot', read_only=True)
    
    class Meta:
        model = AgentRecommendation
        fields = [
            'id',
            'timestamp',
            'recommended_action',
            'explanation_text',
            'confidence',
            'anomaly',
            'plot'
        ]
        read_only_fields = ['timestamp']


class AgentRecommendationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with full relationships."""
    
    anomaly = AnomalyEventSerializer(source='anomaly_event', read_only=True)
    plot = PlotSerializer(source='anomaly_event.plot', read_only=True)
    farm_id = serializers.IntegerField(
        source='anomaly_event.plot.farm.id',
        read_only=True
    )
    
    class Meta:
        model = AgentRecommendation
        fields = [
            'id',
            'timestamp',
            'recommended_action',
            'explanation_text',
            'confidence',
            'anomaly',
            'plot',
            'farm_id'
        ]


class AgentStatisticsSerializer(serializers.Serializer):
    """Serializer for agent statistics response."""
    
    total_recommendations = serializers.IntegerField()
    unprocessed_anomalies = serializers.IntegerField()
    recent_activity_24h = serializers.IntegerField()
    urgency_distribution = serializers.DictField()
    confidence_distribution = serializers.DictField()
    most_common_actions = serializers.ListField()


class ProcessAnomalyRequestSerializer(serializers.Serializer):
    """Serializer for process anomaly request."""
    
    force = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Force reprocessing even if recommendation exists"
    )


class ProcessAnomalyResponseSerializer(serializers.Serializer):
    """Serializer for process anomaly response."""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    recommendation_id = serializers.IntegerField(required=False)
    recommendation = AgentRecommendationSerializer(required=False)


class BatchProcessResponseSerializer(serializers.Serializer):
    """Serializer for batch process response."""
    
    success = serializers.BooleanField()
    statistics = serializers.DictField()


class HealthCheckSerializer(serializers.Serializer):
    """Serializer for health check response."""
    
    status = serializers.CharField()
    service = serializers.CharField()
    timestamp = serializers.DateTimeField()
    details = serializers.DictField()