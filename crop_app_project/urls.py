from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("crop_app.urls")),
]
# Gestion des erreurs
handler404 = 'crop_app.views.error_404'
handler500 = 'crop_app.views.error_500'

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)