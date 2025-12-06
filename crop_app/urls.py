# crop_app/urls.py
from django.urls import path
from .views import (          
    SensorReadingListCreate,
    AnomalyList,
    RecommendationList
)

urlpatterns = [
    path('sensor-readings/', SensorReadingListCreate.as_view()),
    path('anomalies/', AnomalyList.as_view()),
    path('recommendations/', RecommendationList.as_view()),
]