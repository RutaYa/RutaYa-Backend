# rutaya/urls.py - Versión simplificada (REEMPLAZAR todo el contenido)
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserProfileView,
    logout_view
)

# Configuración de Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="Rutaya API",
        default_version='v1',
        description="API Backend para Rutaya - Sistema de gestión de rutas",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@rutaya.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Endpoints - Autenticación
    path('api/v1/auth/register/', UserRegistrationView.as_view(), name='user-register'),
    path('api/v1/auth/login/', UserLoginView.as_view(), name='user-login'),
    path('api/v1/auth/logout/', logout_view, name='user-logout'),
    path('api/v1/auth/profile/', UserProfileView.as_view(), name='user-profile'),

    # Documentación API
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),  # Página principal
]