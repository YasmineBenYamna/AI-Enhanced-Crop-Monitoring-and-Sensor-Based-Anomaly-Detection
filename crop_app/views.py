# crop_app/api_views.py
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import render  # 👈 AJOUTER cette ligne
from .models import SensorReading, AnomalyEvent, AgentRecommendation
from .serializers import (
    SensorReadingSerializer, AnomalyEventSerializer, AgentRecommendationSerializer
)
from django.shortcuts import render

# ========== VUE TEMPLATE HTML ==========
def index(request):
    return render(request, 'index.html')

def charts(request):
    return render(request, 'charts.html')

def widgets(request):
    return render(request, 'widgets.html')

def colors(request):
    return render(request, 'colors.html')

def typography(request):
    return render(request, 'typography.html')

def login_page(request):
    return render(request, 'login.html')

def register(request):
    return render(request, 'register.html')

# Pages d'erreur
def error_404(request, exception):
    return render(request, '404.html', status=404)

def error_500(request):
    return render(request, '500.html', status=500)

def error_404_page(request):
    return render(request, '404.html')

def error_500_page(request):
    return render(request, '500.html')


# ========== VUES API REST ==========
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