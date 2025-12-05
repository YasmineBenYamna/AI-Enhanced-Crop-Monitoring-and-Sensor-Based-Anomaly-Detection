# crop_app/urls.py
from django.urls import path
from .views import (          
    SensorReadingListCreate,
    AnomalyList,
    RecommendationList
)

urlpatterns = [
    path('api/sensor-readings/', SensorReadingListCreate.as_view()),
    path('api/anomalies/', AnomalyList.as_view()),
    path('api/recommendations/', RecommendationList.as_view()),
]