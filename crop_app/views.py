from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .models import FarmProfile, FieldPlot, SensorReading, AnomalyEvent, AgentRecommendation
from .serializers import (
    FarmProfileSerializer,
    FieldPlotSerializer,
    SensorReadingSerializer,
    AnomalyEventSerializer,
    AgentRecommendationSerializer
)


class FarmProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for FarmProfile model
    Provides CRUD operations for farms
    """
    queryset = FarmProfile.objects.all()
    serializer_class = FarmProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Allow filtering by owner or location"""
        queryset = super().get_queryset()
        owner = self.request.query_params.get('owner', None)
        location = self.request.query_params.get('location', None)

        if owner:
            queryset = queryset.filter(owner__icontains=owner)
        if location:
            queryset = queryset.filter(location__icontains=location)

        return queryset


class FieldPlotViewSet(viewsets.ModelViewSet):
    """
    ViewSet for FieldPlot model
    Provides CRUD operations for field plots
    """
    queryset = FieldPlot.objects.select_related('farm').all()
    serializer_class = FieldPlotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Allow filtering by farm"""
        queryset = super().get_queryset()
        farm_id = self.request.query_params.get('farm', None)

        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)

        return queryset

    @action(detail=True, methods=['get'])
    def sensor_summary(self, request, pk=None):
        """
        Get summary of sensor readings for a specific plot
        """
        plot = self.get_object()
        readings = plot.sensor_readings.all()[:100]

        summary = {
            'plot_id': plot.id,
            'plot_name': plot.plot_name,
            'total_readings': readings.count(),
            'latest_readings': SensorReadingSerializer(readings[:10], many=True).data
        }

        return Response(summary)


class SensorReadingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SensorReading model
    Handles sensor data ingestion and retrieval
    """
    queryset = SensorReading.objects.select_related('plot').all()
    serializer_class = SensorReadingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Allow filtering by plot, sensor_type, and time range"""
        queryset = super().get_queryset()

        plot_id = self.request.query_params.get('plot', None)
        sensor_type = self.request.query_params.get('sensor_type', None)

        if plot_id:
            queryset = queryset.filter(plot_id=plot_id)
        if sensor_type:
            queryset = queryset.filter(sensor_type=sensor_type)

        # Limit to recent readings for performance (last 1000)
        return queryset[:1000]

    def create(self, request, *args, **kwargs):
        """
        Override create to handle data ingestion
        This is where ML model will be triggered in Week 2
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # TODO: Week 2 - Trigger ML model processing here
        # Example: detect_anomaly(serializer.instance)

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Bulk create sensor readings (useful for simulator)
        POST /api/sensor-readings/bulk_create/
        Body: [{"plot_id": 1, "sensor_type": "moisture", "value": 45.5}, ...]
        """
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(
            {
                'message': f'{len(serializer.data)} sensor readings created successfully',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class AnomalyEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AnomalyEvent model
    Manages detected anomalies
    """
    queryset = AnomalyEvent.objects.select_related('plot__farm').prefetch_related('recommendation').all()
    serializer_class = AnomalyEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Allow filtering by plot, severity, anomaly_type"""
        queryset = super().get_queryset()

        plot_id = self.request.query_params.get('plot', None)
        severity = self.request.query_params.get('severity', None)
        anomaly_type = self.request.query_params.get('anomaly_type', None)

        if plot_id:
            queryset = queryset.filter(plot_id=plot_id)
        if severity:
            queryset = queryset.filter(severity=severity)
        if anomaly_type:
            queryset = queryset.filter(anomaly_type__icontains=anomaly_type)

        return queryset[:100]  # Limit results

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent anomalies (last 24 hours)
        GET /api/anomalies/recent/
        """
        from django.utils import timezone
        from datetime import timedelta

        last_24h = timezone.now() - timedelta(hours=24)
        anomalies = self.get_queryset().filter(timestamp__gte=last_24h)

        serializer = self.get_serializer(anomalies, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_severity(self, request):
        """
        Get anomalies grouped by severity
        GET /api/anomalies/by_severity/
        """
        from django.db.models import Count

        severity_counts = self.get_queryset().values('severity').annotate(count=Count('id'))

        return Response({
            'severity_breakdown': list(severity_counts),
            'total': sum(item['count'] for item in severity_counts)
        })


class AgentRecommendationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AgentRecommendation model
    Manages AI-generated recommendations
    """
    queryset = AgentRecommendation.objects.select_related('anomaly_event__plot').all()
    serializer_class = AgentRecommendationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Allow filtering by anomaly_event or confidence"""
        queryset = super().get_queryset()

        anomaly_id = self.request.query_params.get('anomaly', None)
        min_confidence = self.request.query_params.get('min_confidence', None)

        if anomaly_id:
            queryset = queryset.filter(anomaly_event_id=anomaly_id)
        if min_confidence:
            try:
                min_conf = float(min_confidence)
                queryset = queryset.filter(confidence__gte=min_conf)
            except ValueError:
                pass

        return queryset[:100]

    @action(detail=False, methods=['get'])
    def high_priority(self, request):
        """
        Get high-priority recommendations (confidence >= 0.8)
        GET /api/recommendations/high_priority/
        """
        recommendations = self.get_queryset().filter(confidence__gte=0.8)
        serializer = self.get_serializer(recommendations, many=True)

        return Response({
            'count': recommendations.count(),
            'recommendations': serializer.data
        })