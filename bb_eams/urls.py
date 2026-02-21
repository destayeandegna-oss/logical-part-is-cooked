from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.conf import settings
from rest_framework import permissions
from django.views.generic import RedirectView
from django.conf.urls.static import static

urlpatterns = [
    path('', RedirectView.as_view(url='/swagger/', permanent=False)),
    path('api/leave/', include('apps.leave.urls')),
    path('api/accounts/', include('apps.accounts.urls')),

    # Auth views for the browsable API and Swagger
    path('accounts/', include('rest_framework.urls')),

    path('admin/', admin.site.urls),

    # Swagger documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)