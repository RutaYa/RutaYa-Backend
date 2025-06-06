# rutaya/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Category, Destination


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


class CategorySerializer(serializers.ModelSerializer):
    destinations_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'destinations_count']

    def get_destinations_count(self, obj):
        return obj.destinations.count()


class DestinationSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Destination
        fields = [
            'id',
            'name',
            'location',
            'image_url',
            'category',
            'category_name',
            'description',
            'created_at',
            'updated_at'
        ]


class DestinationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ['name', 'location', 'image_url', 'category', 'description']