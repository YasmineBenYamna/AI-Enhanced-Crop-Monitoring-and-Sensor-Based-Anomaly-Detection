from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'farms', views.FarmProfileViewSet, basename='farm')
router.register(r'plots', views.FieldPlotViewSet, basename='plot')
router.register(r'sensor-readings', views.SensorReadingViewSet, basename='sensor-reading')
router.register(r'anomalies', views.AnomalyEventViewSet, basename='anomaly')
router.register(r'recommendations', views.AgentRecommendationViewSet, basename='recommendation')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]