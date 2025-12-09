"""
ML Module - URL Configuration (ViewSet Version)
Routes for ML anomaly detection API using ViewSets and routers.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'ml_module'

# Create router and register ViewSet
router = DefaultRouter()
router.register(r'', views.MLViewSet, basename='ml')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]

"""
This creates the following endpoints (assuming main urls.py includes this at 'ml/'):

POST   /ml/train/         - Train anomaly detection model
POST   /ml/detect/        - Detect anomalies (single)
POST   /ml/batch-detect/  - Detect anomalies (batch)
GET    /ml/status/        - Get model training status

The router automatically handles:
- URL pattern generation
- Endpoint naming
- API browsable interface
"""