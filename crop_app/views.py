# crop_app/api_views.py
from rest_framework import generics
from .models import SensorReading, AnomalyEvent, AgentRecommendation
from .serializers import (
    SensorReadingSerializer, AnomalyEventSerializer, AgentRecommendationSerializer
)

# POST /api/sensor-readings/ + GET with ?plot=
class SensorReadingListCreate(generics.ListCreateAPIView):
    queryset = SensorReading.objects.all().order_by('-timestamp')
    serializer_class = SensorReadingSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        plot_id = self.request.query_params.get('plot')
        if plot_id:
            queryset = queryset.filter(plot_id=plot_id)
        return queryset


# GET /api/anomalies/
class AnomalyList(generics.ListAPIView):
    queryset = AnomalyEvent.objects.all().order_by('-timestamp')
    serializer_class = AnomalyEventSerializer


# GET /api/recommendations/
class RecommendationList(generics.ListAPIView):
    queryset = AgentRecommendation.objects.all().order_by('-timestamp')
    serializer_class = AgentRecommendationSerializer