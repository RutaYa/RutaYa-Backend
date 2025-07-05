# rutaya/urls.py - Versión simplificada (REEMPLAZAR todo el contenido)
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .views import *
from . import views

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
    path('api/v1/user/update/<int:pk>', UserUpdateView.as_view(), name='user-update'),
    path('api/v1/user/change-password/<int:user_id>', ChangePasswordView.as_view(), name='change-password'),


    path('api/v1/categories/<int:user_id>/', get_categories_with_destinations, name='categories-destinations'),

    path('api/v1/home/<int:user_id>/', get_home_data, name='home-data'),

    path('api/v1/favorites/add/', AddToFavoritesView.as_view(), name='add-favorite'),
    path('api/v1/favorites/remove/', RemoveFromFavoritesView.as_view(), name='remove-favorite'),

    path('api/v1/community/list/', GetAllRatesView.as_view(), name='community-list'),

    path('api/v1/rate-destinations/add/', CreateDestinationRateView.as_view(), name='rate-destination'),
    path('api/v1/rate-destinations/list/', GetAllDestinationRatesView.as_view(), name='get-destinations-rates'),
    path('api/v1/rate-destinations/delete/<int:rate_id>/', DeleteDestinationRateView.as_view(), name='remove-destination-rate'),

    path('api/v1/rate-package/add/', CreateTourPackageRateView.as_view(), name='rate-package'),
    path('api/v1/rate-package/list/', GetAllTourPackageRatesView.as_view(), name='get-package-rates'),
    path('api/v1/rate-package/delete/<int:rate_id>/', DeleteTourPackageRateView.as_view(), name='remove-package-rate'),


    # En tu urls.py
    path('api/v1/travels/add/', save_travel_availability, name='save-travel-availability'),
    path('api/v1/travels/user/<int:user_id>/', get_travel_availability, name='get-travel-availability'),

    path('api/v1/content/generate/', ProcessIaMessageView.as_view(), name='generate-content'),

    path('api/v1/preferences/', views.save_user_preferences, name='save_user_preferences'),
    path('api/v1/preferences/<int:user_id>/', views.get_user_preferences, name='get_user_preferences'),

    path('api/v1/tour/user/<int:user_id>/', views.get_user_tour_packages, name='get_user_tour_package'),
    path('api/v1/tour/add/', save_tour_package, name='save-tour-package'),
    path('api/v1/tour/pay/<int:pk>/', mark_package_as_paid, name='mark-package-paid'),
    path('api/v1/tour/delete/<int:pk>/', delete_tour_package, name='delete-tour-package'),


    # Documentación API
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),  # Página principal
]