from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from crop_app.views import SensorReadingListCreate, AnomalyList, RecommendationList
from django.contrib import admin
urlpatterns = [
    # JWT Authentication endpoints
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/', admin.site.urls),
    path('api/', include('crop_app.urls')), 
    path('api/ml/', include('ml_module.urls')), 
    path('api/agent/', include('ai_agent.urls')),

]

    
    
