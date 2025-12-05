from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from crop_app.views import SensorReadingListCreate, AnomalyList, RecommendationList

urlpatterns = [
    # JWT Authentication endpoints
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API endpoints
    path('sensor-readings/', SensorReadingListCreate.as_view(), name='sensor-reading-list'),
    path('anomalies/', AnomalyList.as_view(), name='anomaly-list'),
    path('recommendations/', RecommendationList.as_view(), name='recommendation-list'),
]
