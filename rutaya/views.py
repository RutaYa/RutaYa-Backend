# rutaya/views.py
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer, FavoriteActionSerializer
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from .models import Category, Destination
from django.db import models
from django.db.models import Q
from .models import User, Category, Destination, Favorite

class UserRegistrationView(generics.CreateAPIView):
    """
    Vista para registro de usuarios
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)

    @swagger_auto_schema(
        operation_description="Registrar un nuevo usuario",
        responses={
            201: openapi.Response(
                description="Usuario creado exitosamente",
                schema=UserSerializer
            ),
            400: "Error de validación"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)

            return Response({
                'message': 'Usuario registrado exitosamente',
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'preferences': {}
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = (AllowAny,)

    @swagger_auto_schema(
        operation_description="Iniciar sesión de usuario",
        responses={
            200: openapi.Response(
                description="Login exitoso",
                examples={
                    "application/json": {
                        "message": "Login exitoso",
                        "user": {
                            "id": 1,
                            "username": "usuario",
                            "email": "usuario@example.com"
                        },
                        "tokens": {
                            "refresh": "token_refresh",
                            "access": "token_access"
                        }
                    }
                }
            ),
            400: "Credenciales inválidas"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)

            return Response({
                'message': 'Login exitoso',
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Agregar esta vista a tu views.py
@api_view(['GET'])
@permission_classes([AllowAny])
@swagger_auto_schema(
    operation_description="Obtener categorías con destinos y estado de favoritos por usuario",
    manual_parameters=[
        openapi.Parameter(
            'user_id',
            openapi.IN_PATH,
            description="ID del usuario para verificar favoritos",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="Categorías con destinos obtenidas exitosamente",
            examples={
                "application/json": {
                    "message": "Categorías obtenidas exitosamente",
                    "categories": [
                        {
                            "id": 1,
                            "name": "Playas",
                            "destinations": [
                                {
                                    "id": 1,
                                    "name": "Playa Bonita",
                                    "location": "Cancún",
                                    "description": "Una hermosa playa con aguas cristalinas",
                                    "image_url": "https://example.com/playa.jpg",
                                    "isFavorite": True
                                },
                                {
                                    "id": 2,
                                    "name": "Playa del Carmen",
                                    "location": "Riviera Maya",
                                    "description": "Playa con ambiente nocturno",
                                    "image_url": "https://example.com/carmen.jpg",
                                    "isFavorite": False
                                }
                            ]
                        }
                    ]
                }
            }
        ),
        404: "Usuario no encontrado"
    }
)
def get_categories_with_destinations(request, user_id):
    """
    Vista para obtener categorías con destinos y estado de favoritos
    """
    try:
        # Verificar que el usuario existe
        user = get_object_or_404(User, id=user_id)

        # Obtener todas las categorías con sus destinos
        categories = Category.objects.prefetch_related('destinations').all()

        # Obtener los IDs de destinos favoritos del usuario
        favorite_destination_ids = set(
            Favorite.objects.filter(user=user).values_list('destination_id', flat=True)
        )

        # Construir la respuesta
        categories_data = []

        for category in categories:
            destinations_data = []

            for destination in category.destinations.all():
                destination_dict = {
                    'id': destination.id,
                    'name': destination.name,
                    'location': destination.location,
                    'description': destination.description,
                    'image_url': destination.image_url,
                    'isFavorite': destination.id in favorite_destination_ids
                }
                destinations_data.append(destination_dict)

            category_dict = {
                'id': category.id,
                'name': category.name,
                'destinations': destinations_data
            }
            categories_data.append(category_dict)

        return Response({
            'message': 'Categorías obtenidas exitosamente',
            'categories': categories_data
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'error': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AddToFavoritesView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=FavoriteActionSerializer,
        operation_description="Agregar destino a favoritos",
        responses={
            201: openapi.Response(
                description="Destino agregado a favoritos exitosamente",
                examples={
                    "application/json": {
                        "message": "Destino agregado a favoritos exitosamente",
                        "favorite": {
                            "id": 1,
                            "userId": 1,
                            "destinationId": 5,
                            "destination_name": "Playa Bonita",
                            "user_email": "usuario@example.com"
                        }
                    }
                }
            ),
            400: "Error de validación o destino ya está en favoritos",
        }
    )
    def post(self, request):
        serializer = FavoriteActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_id = serializer.validated_data['userId']
        destination_id = serializer.validated_data['destinationId']

        user = User.objects.get(id=user_id)
        destination = Destination.objects.get(id=destination_id)

        if Favorite.objects.filter(user=user, destination=destination).exists():
            return Response({
                'error': 'Este destino ya está en favoritos'
            }, status=status.HTTP_400_BAD_REQUEST)

        favorite = Favorite.objects.create(user=user, destination=destination)

        return Response({
            'message': 'Destino agregado a favoritos exitosamente',
            'favorite': {
                'id': favorite.id,
                'userId': user.id,
                'destinationId': destination.id,
                'destination_name': destination.name,
                'user_email': user.email
            }
        }, status=status.HTTP_201_CREATED)

class RemoveFromFavoritesView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=FavoriteActionSerializer,
        operation_description="Eliminar destino de favoritos",
        responses={
            200: openapi.Response(
                description="Destino eliminado de favoritos exitosamente",
                examples={
                    "application/json": {
                        "message": "Destino eliminado de favoritos exitosamente",
                        "removed": {
                            "userId": 1,
                            "destinationId": 5,
                            "destination_name": "Playa Bonita",
                            "user_email": "usuario@example.com"
                        }
                    }
                }
            ),
            400: "Error de validación",
            404: "Favorito no encontrado"
        }
    )
    def delete(self, request):
        serializer = FavoriteActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_id = serializer.validated_data['userId']
        destination_id = serializer.validated_data['destinationId']

        user = User.objects.get(id=user_id)
        destination = Destination.objects.get(id=destination_id)

        try:
            favorite = Favorite.objects.get(user=user, destination=destination)
            favorite.delete()

            return Response({
                'message': 'Destino eliminado de favoritos exitosamente',
                'removed': {
                    'userId': user.id,
                    'destinationId': destination.id,
                    'destination_name': destination.name,
                    'user_email': user.email
                }
            }, status=status.HTTP_200_OK)

        except Favorite.DoesNotExist:
            return Response({
                'error': 'Este destino no está en favoritos'
            }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@swagger_auto_schema(
    operation_description="Cerrar sesión (logout)",
    responses={200: "Logout exitoso"}
)
def logout_view(request):
    """
    Vista para logout - invalida el refresh token
    """
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logout exitoso"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": "Token inválido"}, status=status.HTTP_400_BAD_REQUEST)