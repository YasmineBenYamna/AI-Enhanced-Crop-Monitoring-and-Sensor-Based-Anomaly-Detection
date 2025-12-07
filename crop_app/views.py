# crop_app/api_views.py
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import SensorReading, AnomalyEvent, AgentRecommendation
from .serializers import (
    SensorReadingSerializer, AnomalyEventSerializer, AgentRecommendationSerializer
)

# POST /api/sensor-readings/ + GET with ?plot=
class SensorReadingListCreate(generics.ListCreateAPIView):
    queryset = SensorReading.objects.all().order_by('-timestamp')
    serializer_class = SensorReadingSerializer
     
    def get_permissions(self):
        """
        POST (simulator ingestion) = AllowAny
        GET (dashboard viewing) = IsAuthenticated
        """
        if self.request.method == 'POST':
            return [AllowAny()]  # Simulator can POST without auth
        return [IsAuthenticated()]  # Dashboard needs JWT to GET

    def get_queryset(self):
        queryset = super().get_queryset() 
       # Only filter by user for authenticated requests (GET)
        if self.request.user.is_authenticated and not self.request.user.is_staff:
            queryset = queryset.filter(plot__farm__owner=self.request.user)
            
        plot_id = self.request.query_params.get('plot') 
        if plot_id:
            queryset = queryset.filter(plot_id=plot_id)
        return queryset


# GET /api/anomalies/
class AnomalyList(generics.ListAPIView):
    queryset = AnomalyEvent.objects.all().order_by('-timestamp')
    serializer_class = AnomalyEventSerializer
    permission_classes = [IsAuthenticated] # Require authentication for viewing data

    def get_queryset(self):# Restrict to user's farm plots
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(plot__farm__owner=self.request.user)
        return queryset
        
# GET /api/recommendations/
class RecommendationList(generics.ListAPIView):
    queryset = AgentRecommendation.objects.all().order_by('-timestamp')
    serializer_class = AgentRecommendationSerializer
    permission_classes = [IsAuthenticated]  # Require authentication for viewing data

    def get_queryset(self):  # Restrict to user's farm plots
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(plot_event__plot__farm__owner=self.request.user)
        return queryset