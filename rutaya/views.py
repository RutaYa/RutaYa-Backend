# rutaya/views.py
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import User
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from .models import Category, Destination
from .serializers import CategorySerializer, DestinationSerializer, DestinationCreateSerializer
from django.db import models
from django.db.models import Q


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

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


@swagger_auto_schema(
    method='GET',
    operation_description="Obtener todas las categorías",
    responses={200: CategorySerializer(many=True)}
)
@swagger_auto_schema(
    method='POST',
    operation_description="Crear nueva categoría",
    request_body=CategorySerializer,
    responses={
        201: openapi.Response('Category created successfully', CategorySerializer),
        400: 'Bad Request'
    }
)
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def category_list(request):
    """
    GET: Obtener todas las categorías
    POST: Crear nueva categoría
    """

    if request.method == 'GET':
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Categories retrieved successfully'
        })

    elif request.method == 'POST':
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Category created successfully'
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors,
            'message': 'Error creating category'
        }, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='GET',
    operation_description="Obtener categoría por ID",
    responses={200: CategorySerializer}
)
@swagger_auto_schema(
    method='PUT',
    operation_description="Actualizar categoría",
    request_body=CategorySerializer,
    responses={
        200: openapi.Response('Category updated successfully', CategorySerializer),
        400: 'Bad Request',
        404: 'Not Found'
    }
)
@swagger_auto_schema(
    method='DELETE',
    operation_description="Eliminar categoría",
    responses={
        204: 'Category deleted successfully',
        404: 'Not Found'
    }
)
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([AllowAny])
def category_detail(request, pk):
    """
    GET: Obtener categoría por ID
    PUT: Actualizar categoría
    DELETE: Eliminar categoría
    """
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'GET':
        serializer = CategorySerializer(category)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Category retrieved successfully'
        })

    elif request.method == 'PUT':
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Category updated successfully'
            })
        return Response({
            'success': False,
            'errors': serializer.errors,
            'message': 'Error updating category'
        }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        category.delete()
        return Response({
            'success': True,
            'message': 'Category deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


# ============ DESTINATION VIEWS ============

@swagger_auto_schema(
    method='GET',
    operation_description="Obtener todos los destinos con filtros opcionales",
    manual_parameters=[
        openapi.Parameter('category_id', openapi.IN_QUERY, description="ID de categoría", type=openapi.TYPE_INTEGER),
        openapi.Parameter('location', openapi.IN_QUERY, description="Ubicación", type=openapi.TYPE_STRING),
        openapi.Parameter('search', openapi.IN_QUERY, description="Buscar en nombre o descripción",
                          type=openapi.TYPE_STRING),
    ],
    responses={200: DestinationSerializer(many=True)}
)
@swagger_auto_schema(
    method='POST',
    operation_description="Crear nuevo destino",
    request_body=DestinationCreateSerializer,
    responses={
        201: openapi.Response('Destination created successfully', DestinationSerializer),
        400: 'Bad Request'
    }
)
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def destination_list(request):
    """
    GET: Obtener todos los destinos (con paginación y filtros)
    POST: Crear nuevo destino
    """
    if request.method == 'GET':
        destinations = Destination.objects.select_related('category').all()

        # Filtros opcionales
        category_id = request.GET.get('category_id')
        location = request.GET.get('location')
        search = request.GET.get('search')

        if category_id:
            destinations = destinations.filter(category_id=category_id)

        if location:
            destinations = destinations.filter(location__icontains=location)

        if search:
            destinations = destinations.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        # Paginación
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(destinations, request)

        if page is not None:
            serializer = DestinationSerializer(page, many=True)
            return paginator.get_paginated_response({
                'success': True,
                'data': serializer.data,
                'message': 'Destinations retrieved successfully'
            })

        serializer = DestinationSerializer(destinations, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Destinations retrieved successfully'
        })

    elif request.method == 'POST':
        serializer = DestinationCreateSerializer(data=request.data)
        if serializer.is_valid():
            destination = serializer.save()
            response_serializer = DestinationSerializer(destination)
            return Response({
                'success': True,
                'data': response_serializer.data,
                'message': 'Destination created successfully'
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors,
            'message': 'Error creating destination'
        }, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='GET',
    operation_description="Obtener destino por ID",
    responses={200: DestinationSerializer}
)
@swagger_auto_schema(
    method='PUT',
    operation_description="Actualizar destino",
    request_body=DestinationCreateSerializer,
    responses={
        200: openapi.Response('Destination updated successfully', DestinationSerializer),
        400: 'Bad Request',
        404: 'Not Found'
    }
)
@swagger_auto_schema(
    method='DELETE',
    operation_description="Eliminar destino",
    responses={
        204: 'Destination deleted successfully',
        404: 'Not Found'
    }
)
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([AllowAny])
def destination_detail(request, pk):
    """
    GET: Obtener destino por ID
    PUT: Actualizar destino
    DELETE: Eliminar destino
    """
    destination = get_object_or_404(Destination, pk=pk)

    if request.method == 'GET':
        serializer = DestinationSerializer(destination)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Destination retrieved successfully'
        })

    elif request.method == 'PUT':
        serializer = DestinationCreateSerializer(destination, data=request.data)
        if serializer.is_valid():
            destination = serializer.save()
            response_serializer = DestinationSerializer(destination)
            return Response({
                'success': True,
                'data': response_serializer.data,
                'message': 'Destination updated successfully'
            })
        return Response({
            'success': False,
            'errors': serializer.errors,
            'message': 'Error updating destination'
        }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        destination.delete()
        return Response({
            'success': True,
            'message': 'Destination deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(
    method='GET',
    operation_description="Obtener destinos por categoría específica",
    responses={200: DestinationSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def destinations_by_category(request, category_id):
    """
    Obtener destinos por categoría específica
    """
    category = get_object_or_404(Category, pk=category_id)
    destinations = Destination.objects.filter(category=category)

    # Paginación
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(destinations, request)

    if page is not None:
        serializer = DestinationSerializer(page, many=True)
        return paginator.get_paginated_response({
            'success': True,
            'data': serializer.data,
            'category': category.name,
            'message': f'Destinations for category "{category.name}" retrieved successfully'
        })

    serializer = DestinationSerializer(destinations, many=True)
    return Response({
        'success': True,
        'data': serializer.data,
        'category': category.name,
        'message': f'Destinations for category "{category.name}" retrieved successfully'
    })


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    @swagger_auto_schema(
        operation_description="Obtener perfil del usuario autenticado",
        responses={200: UserSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Actualizar perfil del usuario autenticado",
        responses={200: UserSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)


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