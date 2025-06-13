# rutaya/views.py
from rest_framework import generics
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
import random
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import *
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import User, Category, Destination, Favorite, TravelAvailability
from django.db.models import Count
from rutaya.utils.gemini_api import send_message

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

            # Obtener preferencias del usuario si existen
            preferences_data = None
            try:
                preferences = UserPreferences.objects.get(user=user)
                preferences_serialized = UserPreferencesSerializer(preferences).data
                preferences_serialized.pop('user_id', None)
                preferences_data = preferences_serialized
            except UserPreferences.DoesNotExist:
                preferences_data = None

            return Response({
                'message': 'Login exitoso',
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                "preferences": preferences_data
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


@api_view(['GET'])
@permission_classes([AllowAny])
@swagger_auto_schema(
    operation_description="Obtener todos los datos necesarios para la pantalla Home",
    manual_parameters=[
        openapi.Parameter(
            'user_id',
            openapi.IN_PATH,
            description="ID del usuario para personalizar la experiencia",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="Datos del home obtenidos exitosamente",
            examples={
                "application/json": {
                    "message": "Datos del home obtenidos exitosamente",
                    "suggestions": [
                        {
                            "id": 1,
                            "name": "Playa Bonita",
                            "location": "Cancún",
                            "description": "Una hermosa playa...",
                            "image_url": "https://example.com/playa.jpg",
                            "isFavorite": True
                        }
                    ],
                    "popular": [
                        {
                            "id": 2,
                            "name": "Machu Picchu",
                            "location": "Cusco",
                            "description": "Ciudadela inca...",
                            "image_url": "https://example.com/machu.jpg",
                            "isFavorite": False,
                            "favorites_count": 25
                        }
                    ],
                    "categories": [
                        {
                            "id": 1,
                            "name": "Playas",
                            "destinations": [
                                {
                                    "id": 1,
                                    "name": "Playa Bonita",
                                    "location": "Cancún",
                                    "description": "Una hermosa playa...",
                                    "image_url": "https://example.com/playa.jpg",
                                    "isFavorite": True
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
def get_home_data(request, user_id):
    """
    Vista consolidada para obtener todos los datos del home:
    - Sugerencias para ti (8 destinos random)
    - Más populares (4 destinos más agregados a favoritos)
    - Categorías con destinos ordenadas por ID
    """
    try:
        # Verificar que el usuario existe
        user = get_object_or_404(User, id=user_id)

        # Obtener los IDs de destinos favoritos del usuario
        favorite_destination_ids = set(
            Favorite.objects.filter(user=user).values_list('destination_id', flat=True)
        )

        # 1. SUGERENCIAS PARA TI - 8 destinos random
        all_destinations = list(Destination.objects.all())
        suggestions_destinations = random.sample(
            all_destinations,
            min(8, len(all_destinations))
        )

        suggestions_data = []
        for destination in suggestions_destinations:
            suggestions_data.append({
                'id': destination.id,
                'name': destination.name,
                'location': destination.location,
                'description': destination.description,
                'image_url': destination.image_url,
                'isFavorite': destination.id in favorite_destination_ids
            })

        # 2. MÁS POPULARES - 4 destinos más agregados a favoritos
        # Obtener destinos con count de favoritos, ordenados por popularidad
        popular_destinations = Destination.objects.annotate(
            favorites_count=Count('favorited_by')
        ).order_by('-favorites_count')

        # Tomar los primeros 4 (o los que haya)
        popular_with_favorites = list(popular_destinations.filter(favorites_count__gt=0)[:4])

        # Si faltan destinos, completar con randoms
        if len(popular_with_favorites) < 4:
            remaining_count = 4 - len(popular_with_favorites)
            used_ids = [dest.id for dest in popular_with_favorites]

            available_destinations = [
                dest for dest in all_destinations
                if dest.id not in used_ids
            ]

            if available_destinations:
                random_destinations = random.sample(
                    available_destinations,
                    min(remaining_count, len(available_destinations))
                )

                # Agregar count de favoritos para los randoms
                for dest in random_destinations:
                    dest.favorites_count = Favorite.objects.filter(destination=dest).count()

                popular_with_favorites.extend(random_destinations)

        popular_data = []
        for destination in popular_with_favorites:
            popular_data.append({
                'id': destination.id,
                'name': destination.name,
                'location': destination.location,
                'description': destination.description,
                'image_url': destination.image_url,
                'isFavorite': destination.id in favorite_destination_ids,
                'favorites_count': getattr(destination, 'favorites_count', 0)
            })

        # 3. CATEGORÍAS CON DESTINOS - ordenadas por ID ascendente
        categories = Category.objects.prefetch_related('destinations').order_by('id')

        categories_data = []
        for category in categories:
            destinations_data = []

            # Ordenar destinos por ID ascendente también
            for destination in category.destinations.order_by('id'):
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
            'message': 'Datos del home obtenidos exitosamente',
            'suggestions': suggestions_data,
            'popular': popular_data,
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
@permission_classes([AllowAny])  # Permitir acceso sin autenticación
def save_travel_availability(request):
    """
    Vista para guardar múltiples fechas de disponibilidad de viaje usando userId.
    """
    try:

        # Usar el serializer para validar y procesar los datos
        serializer = TravelAvailabilitySerializer(data=request.data)

        if serializer.is_valid():

            # El serializer ya maneja toda la lógica
            validated_data = serializer.save()

            response_data = {
                "message": f"Fechas guardadas exitosamente para el usuario {validated_data['userId']}",
                "userId": validated_data['userId'],
                "dates": [str(date) for date in validated_data['dates']]
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        else:
            return Response(
                {"error": "Datos inválidos", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        print("❌ Error inesperado:", e)
        import traceback
        traceback.print_exc()
        return Response(
            {"error": "Error interno del servidor", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
@swagger_auto_schema(
    operation_description="Obtener fechas de disponibilidad de viaje de un usuario",
    manual_parameters=[
        openapi.Parameter(
            'user_id',
            openapi.IN_PATH,
            description="ID del usuario",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="Fechas obtenidas exitosamente",
            examples={
                "application/json": {
                    "userId": 5,
                    "dates": [
                        "2024-07-01",
                        "2024-07-02",
                        "2024-07-03"
                    ]
                }
            }
        ),
        404: "Usuario no encontrado",
        500: "Error interno del servidor"
    }
)
def get_travel_availability(request, user_id):
    """
    Vista para obtener fechas de disponibilidad de viaje de un usuario.
    """
    try:
        user = get_object_or_404(User, id=user_id)

        # Obtener fechas ordenadas
        travel_dates = TravelAvailability.objects.filter(user=user).order_by('date')

        dates = [availability.date.isoformat() for availability in travel_dates]

        return Response({
            "userId": user.id,
            "dates": dates
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": "Error interno del servidor",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProcessIaMessageView(generics.CreateAPIView):
    serializer_class = messageInputSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                answer = send_message(serializer.validated_data)
                return Response({"botMessage": answer}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@swagger_auto_schema(
    operation_description="Guardar preferencias de usuario",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['user_id', 'travel_interests', 'adrenaline_level'],
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID del usuario'),
            'birth_date': openapi.Schema(type=openapi.TYPE_STRING, format='date',
                                         description='Fecha de nacimiento (YYYY-MM-DD)'),
            'gender': openapi.Schema(type=openapi.TYPE_STRING, description='Género del usuario'),
            'travel_interests': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                description='Lista de intereses de viaje (máximo 2)'
            ),
            'preferred_environment': openapi.Schema(type=openapi.TYPE_STRING, description='Ambiente preferido'),
            'travel_style': openapi.Schema(type=openapi.TYPE_STRING, description='Estilo de viaje'),
            'budget_range': openapi.Schema(type=openapi.TYPE_STRING, description='Rango de presupuesto'),
            'adrenaline_level': openapi.Schema(type=openapi.TYPE_INTEGER, description='Nivel de adrenalina (1-10)'),
            'wants_hidden_places': openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                                  description='Quiere conocer lugares ocultos'),
        }
    ),
    responses={
        201: openapi.Response(
            description="Preferencias guardadas exitosamente",
            examples={
                "application/json": {
                    "message": "Preferencias guardadas exitosamente para el usuario 5",
                    "userId": 5,
                    "created": True,
                    "preferences": {
                        "birth_date": "1990-05-15",
                        "gender": "Masculino",
                        "travel_interests": ["Aventura", "Cultura"],
                        "preferred_environment": "Montañas",
                        "travel_style": "En pareja",
                        "budget_range": "351 - 700 USD",
                        "adrenaline_level": 7,
                        "wants_hidden_places": True
                    }
                }
            }
        ),
        400: "Datos inválidos",
        500: "Error interno del servidor"
    }
)
def save_user_preferences(request):
    """
    Vista para guardar preferencias de usuario usando userId.
    Si ya existen preferencias, las reemplaza.
    """
    try:
        # Usar el serializer para validar y procesar los datos
        serializer = UserPreferencesSerializer(data=request.data)

        if serializer.is_valid():
            # El serializer ya maneja toda la lógica
            validated_data = serializer.save()

            # Serializar las preferencias para la respuesta
            preferences_data = UserPreferencesSerializer(validated_data['preferences']).data
            # Remover user_id del response ya que no es necesario
            preferences_data.pop('user_id', None)

            response_data = {
                "message": f"Preferencias {'creadas' if validated_data['created'] else 'actualizadas'} exitosamente para el usuario {validated_data['userId']}",
                "userId": validated_data['userId'],
                "created": validated_data['created'],
                "preferences": preferences_data
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        else:
            return Response(
                {"error": "Datos inválidos", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        print("❌ Error inesperado:", e)
        import traceback
        traceback.print_exc()
        return Response(
            {"error": "Error interno del servidor", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
@swagger_auto_schema(
    operation_description="Obtener preferencias de usuario",
    manual_parameters=[
        openapi.Parameter(
            'user_id',
            openapi.IN_PATH,
            description="ID del usuario",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="Preferencias obtenidas exitosamente",
            examples={
                "application/json": {
                    "userId": 5,
                    "preferences": {
                        "birth_date": "1990-05-15",
                        "gender": "masculino",
                        "travel_interests": ["Aventura", "Cultura"],
                        "preferred_environment": "montanas",
                        "travel_style": "pareja",
                        "budget_range": "351_700",
                        "adrenaline_level": 7,
                        "wants_hidden_places": True,
                        "age": 34
                    }
                }
            }
        ),
        404: "Usuario no encontrado o sin preferencias",
        500: "Error interno del servidor"
    }
)
def get_user_preferences(request, user_id):
    """
    Vista para obtener preferencias de usuario.
    """
    try:
        user = get_object_or_404(User, id=user_id)

        try:
            preferences = UserPreferences.objects.get(user=user)

            # Serializar las preferencias
            serializer = UserPreferencesSerializer(preferences)
            preferences_data = serializer.data
            preferences_data.pop('user_id', None)  # Remover user_id del response

            return Response({
                "userId": user.id,
                "preferences": preferences_data
            }, status=status.HTTP_200_OK)

        except UserPreferences.DoesNotExist:
            return Response({
                "error": "El usuario no tiene preferencias guardadas",
                "userId": user.id
            }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            "error": "Error interno del servidor",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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