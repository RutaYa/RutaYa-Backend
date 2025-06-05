# rutaya/views.py
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import User
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer


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