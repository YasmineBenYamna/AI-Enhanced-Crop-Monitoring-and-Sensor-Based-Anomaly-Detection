# crop_app/urls.py
from django.urls import path
from .views import (          # ← now it's .views, not .api_views
    SensorReadingListCreate,
    AnomalyList,
    RecommendationList
)

urlpatterns = [
    path('api/sensor-readings/', SensorReadingListCreate.as_view()),
    path('api/anomalies/', AnomalyList.as_view()),
    path('api/recommendations/', RecommendationList.as_view()),
]