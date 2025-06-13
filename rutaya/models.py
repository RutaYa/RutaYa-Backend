from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    # Mantener username pero hacerlo igual al email
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)

    # Solución para el conflicto de reverse accessors
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='rutaya_users',
        related_query_name='rutaya_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='rutaya_users',
        related_query_name='rutaya_user',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        # Sincronizar username con email
        self.username = self.email
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'users'


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']
        db_table = 'categories'

    def __str__(self):
        return self.name

class TravelAvailability(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='travel_availabilities'
    )
    date = models.DateField()

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['date']
        db_table = 'travel_availabilities'
        verbose_name = 'Travel Availability'
        verbose_name_plural = 'Travel Availabilities'

    def __str__(self):
        return f"{self.user.email} - {self.date}"

class Destination(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=100)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='destinations')
    description = models.TextField()

    class Meta:
        verbose_name = "Destination"
        verbose_name_plural = "Destinations"
        db_table = 'destinations'

    def __str__(self):
        return f"{self.name} - {self.location}"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='favorited_by')

    class Meta:
        unique_together = ('user', 'destination')  # Un usuario no puede marcar el mismo destino dos veces
        verbose_name = "Favorite"
        verbose_name_plural = "Favorites"
        db_table = 'favorites'

    def __str__(self):
        return f"{self.user.username} - {self.destination.name}"

class UserPreferences(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='preferences'
    )
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=50, null=True, blank=True)
    travel_interests = models.JSONField(default=list)  # Cambio aquí
    preferred_environment = models.CharField(max_length=50, null=True, blank=True)
    travel_style = models.CharField(max_length=50, null=True, blank=True)
    budget_range = models.CharField(max_length=50, null=True, blank=True)
    adrenaline_level = models.IntegerField(default=5)
    wants_hidden_places = models.BooleanField(null=True, blank=True)

    class Meta:
        verbose_name = "User Preferences"
        verbose_name_plural = "User Preferences"
        db_table = 'user_preferences'

    def __str__(self):
        return f"Preferencias de {self.user.email}"