# rutaya/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Category, Destination, TravelAvailability, UserPreferences


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name', 'phone')

    def create(self, validated_data):
        # Crear usuario con email como username
        email = validated_data['email']
        validated_data['username'] = email  # Añadir username explícitamente

        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Credenciales inválidas.')
            if not user.is_active:
                raise serializers.ValidationError('Cuenta desactivada.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Debe incluir email y contraseña.')

        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone', 'date_joined')
        read_only_fields = ('id', 'date_joined')


class FavoriteActionSerializer(serializers.Serializer):
    userId = serializers.IntegerField()
    destinationId = serializers.IntegerField()

    def validate_userId(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Usuario no encontrado.")
        return value

    def validate_destinationId(self, value):
        if not Destination.objects.filter(id=value).exists():
            raise serializers.ValidationError("Destino no encontrado.")
        return value

class TravelAvailabilitySerializer(serializers.Serializer):
    userId = serializers.IntegerField()
    dates = serializers.ListField(
        child=serializers.DateField(format="%Y-%m-%d"),
        allow_empty=False
    )

    def validate_userId(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Usuario no encontrado.")
        return value

    def create(self, validated_data):
        user_id = validated_data['userId']
        dates = validated_data['dates']
        user = User.objects.get(id=user_id)

        # Eliminar fechas anteriores (puedes cambiar este comportamiento)
        TravelAvailability.objects.filter(user=user).delete()

        # Crear nuevas fechas
        new_entries = [TravelAvailability(user=user, date=d) for d in dates]
        TravelAvailability.objects.bulk_create(new_entries)

        return validated_data


class messageInputSerializer(serializers.Serializer):
    userId = serializers.IntegerField(required=True)
    currentMessage = serializers.CharField()
    previousMessages = serializers.ListField(
        child=serializers.DictField(), required=False
    )
    memoryBank = serializers.DictField(required=False)



class UserPreferencesSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = UserPreferences
        fields = [
            'user_id', 'birth_date', 'gender', 'travel_interests',
            'preferred_environment', 'travel_style', 'budget_range',
            'adrenaline_level', 'wants_hidden_places'
        ]

    def validate_user_id(self, value):
        """Validar que el usuario existe"""
        try:
            User.objects.get(id=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Usuario no encontrado")

    def validate_travel_interests(self, value):
        """Validar que no se seleccionen más de 2 intereses"""
        if len(value) > 2:
            raise serializers.ValidationError("Solo puedes seleccionar máximo 2 intereses")

        return value

    def validate_adrenaline_level(self, value):
        """Validar que el nivel de adrenalina esté entre 1 y 10"""
        if not (1 <= value <= 10):
            raise serializers.ValidationError("El nivel de adrenalina debe estar entre 1 y 10")
        return value

    def create(self, validated_data):
        """Crear o actualizar preferencias del usuario"""
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)

        # Usar update_or_create para reemplazar si ya existe
        preferences, created = UserPreferences.objects.update_or_create(
            user=user,
            defaults=validated_data
        )

        return {
            'userId': user.id,
            'preferences': preferences,
            'created': created
        }