from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgentRecommendationViewSet

app_name = 'ai_agent'

router = DefaultRouter()
router.register(r'recommendations', AgentRecommendationViewSet, basename='recommendation')

urlpatterns = [
    path('', include(router.urls)),
]