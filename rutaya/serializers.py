# rutaya/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import *
from django.utils import timezone
from django.utils.dateparse import parse_datetime
import pytz
from datetime import datetime
from .models import TourPackage, ItineraryItem


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


class ItineraryItemSerializer(serializers.ModelSerializer):
    datetime = serializers.CharField(max_length=255)  # Campo como string

    class Meta:
        model = ItineraryItem
        fields = ['datetime', 'description', 'order']

    def validate_datetime(self, value):
        """
        Validación básica del formato de datetime como string
        """
        if not isinstance(value, str):
            raise serializers.ValidationError("El datetime debe ser una cadena de texto")

        if not value.strip():
            raise serializers.ValidationError("El datetime no puede estar vacío")

        # Validación opcional: verificar que tenga un formato mínimo válido
        # Puedes comentar esto si quieres total flexibilidad
        if 'T' not in value and ':' not in value:
            raise serializers.ValidationError(
                "El formato debe incluir fecha y hora (ej: 2025-07-17T08:00 o 2025-07-17 08:00)"
            )

        return value.strip()


class TourPackageSerializer(serializers.ModelSerializer):
    itinerary = ItineraryItemSerializer(many=True, required=False)
    start_date = serializers.CharField(max_length=255)  # Campo como string
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = TourPackage
        fields = [
            'id', 'user_id', 'title', 'description', 'start_date',
            'days', 'quantity', 'price', 'is_paid', 'itinerary'
        ]
        read_only_fields = ['id']

    def validate_start_date(self, value):
        """
        Validación básica del formato de start_date como string
        """
        if not isinstance(value, str):
            raise serializers.ValidationError("El start_date debe ser una cadena de texto")

        if not value.strip():
            raise serializers.ValidationError("El start_date no puede estar vacío")

        # Validación opcional: verificar que tenga un formato mínimo válido
        # Puedes comentar esto si quieres total flexibilidad
        if 'T' not in value and ':' not in value:
            raise serializers.ValidationError(
                "El formato debe incluir fecha y hora (ej: 2025-07-17T08:00 o 2025-07-17 08:00)"
            )

        return value.strip()

    def create(self, validated_data):
        itinerary_data = validated_data.pop('itinerary', [])
        user_id = validated_data.pop('user_id')

        # Obtener el usuario
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)

        # Crear el tour package
        tour_package = TourPackage.objects.create(user=user, **validated_data)

        # Crear los itinerary items
        for index, item_data in enumerate(itinerary_data):
            ItineraryItem.objects.create(
                tour_package=tour_package,
                order=index,
                **item_data
            )

        return tour_package

    def update(self, instance, validated_data):
        itinerary_data = validated_data.pop('itinerary', None)

        # Actualizar los campos del tour package
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Si se proporcionan datos de itinerario, actualizar
        if itinerary_data is not None:
            # Eliminar items existentes
            instance.itinerary.all().delete()

            # Crear nuevos items
            for index, item_data in enumerate(itinerary_data):
                ItineraryItem.objects.create(
                    tour_package=instance,
                    order=index,
                    **item_data
                )

        return instance

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone')
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


# Agregar estos serializers a tu archivo serializers.py existente

# Serializers para crear calificaciones (POST)
class DestinationRateCreateSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(write_only=True)
    destinationId = serializers.IntegerField(write_only=True)

    class Meta:
        model = DestinationRate
        fields = ['userId', 'destinationId', 'stars', 'comment', 'created_at']

    def validate_userId(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Usuario no encontrado.")
        return value

    def validate_destinationId(self, value):
        if not Destination.objects.filter(id=value).exists():
            raise serializers.ValidationError("Destino no encontrado.")
        return value

    def create(self, validated_data):
        user_id = validated_data.pop('userId')
        destination_id = validated_data.pop('destinationId')

        user = User.objects.get(id=user_id)
        destination = Destination.objects.get(id=destination_id)

        rate = DestinationRate.objects.create(
            user=user,
            destination=destination,
            **validated_data
        )
        return rate


class TourPackageRateCreateSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(write_only=True)
    tourPackageId = serializers.IntegerField(write_only=True)

    class Meta:
        model = TourPackageRate
        fields = ['userId', 'tourPackageId', 'stars', 'comment', 'created_at']

    def validate_userId(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Usuario no encontrado.")
        return value

    def validate_tourPackageId(self, value):
        if not TourPackage.objects.filter(id=value).exists():
            raise serializers.ValidationError("Paquete turístico no encontrado.")
        return value

    def create(self, validated_data):
        user_id = validated_data.pop('userId')
        tour_package_id = validated_data.pop('tourPackageId')

        user = User.objects.get(id=user_id)
        tour_package = TourPackage.objects.get(id=tour_package_id)

        rate = TourPackageRate.objects.create(
            user=user,
            tour_package=tour_package,
            **validated_data
        )
        return rate


# Serializers para mostrar calificaciones (GET)
class DestinationRateSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    destination = serializers.SerializerMethodField()

    class Meta:
        model = DestinationRate
        fields = ['id', 'user', 'destination', 'stars', 'comment', 'created_at']

    def get_destination(self, obj):
        return {
            'id': obj.destination.id,
            'name': obj.destination.name,
            'location': obj.destination.location,
            'description': obj.destination.description,
            'image_url': obj.destination.image_url
        }


class TourPackageRateSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    tour_package = serializers.SerializerMethodField()

    class Meta:
        model = TourPackageRate
        fields = ['id', 'user', 'tour_package', 'stars', 'comment', 'created_at']

    def get_tour_package(self, obj):
        itinerary = ItineraryItemSerializer(obj.tour_package.itinerary.all(), many=True).data
        return {
            'id': obj.tour_package.id,
            'title': obj.tour_package.title,
            'description': obj.tour_package.description,
            'start_date': obj.tour_package.start_date,
            'quantity': obj.tour_package.quantity,
            'days': obj.tour_package.days,
            'price': obj.tour_package.price,
            'is_paid': obj.tour_package.is_paid,
            'itinerary': itinerary
        }