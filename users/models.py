from django.contrib.auth.models import AbstractUser
from django.db import models
from routes.models import Waypoint  # Импортируем модель точек маршрута


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('tourist', 'Турист'),
        ('guide', 'Гид'),
        ('operator', 'Оператор маршрутов'),
        ('admin', 'Администратор'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='tourist',
        verbose_name="Роль"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Телефон"
    )
    avatar = models.ImageField(
        upload_to='users/avatars/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name="Аватар"
    )
    bio = models.TextField(
        blank=True,
        verbose_name="О себе"
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class FavoriteWaypoint(models.Model):
    PRIORITY_CHOICES = [
        (1, '⭐ Низкий'),
        (2, '⭐⭐ Средний'),
        (3, '⭐⭐⭐ Высокий'),
        (4, '⭐⭐⭐⭐ Очень высокий'),
        (5, '⭐⭐⭐⭐⭐ Обязательно посетить'),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name="Пользователь"
    )
    waypoint = models.ForeignKey(
        Waypoint,
        on_delete=models.CASCADE,
        verbose_name="Точка маршрута"
    )
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=3,
        verbose_name="Приоритет"
    )
    planned_visit_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Планируемая дата посещения"
    )
    personal_notes = models.TextField(
        blank=True,
        verbose_name="Персональные заметки"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Избранная точка"
        verbose_name_plural = "Избранные точки"
        unique_together = ['user', 'waypoint']  # Одна точка может быть в избранном только один раз у пользователя

    def __str__(self):
        return f"{self.user.username} - {self.waypoint.name}"


class VisitNote(models.Model):
    RATING_CHOICES = [
        (1, '⭐'),
        (2, '⭐⭐'),
        (3, '⭐⭐⭐'),
        (4, '⭐⭐⭐⭐'),
        (5, '⭐⭐⭐⭐⭐'),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='visit_notes'
    )
    waypoint = models.ForeignKey(
        Waypoint,
        on_delete=models.CASCADE
    )
    visit_date = models.DateField(verbose_name="Дата посещения")
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        verbose_name="Оценка"
    )
    notes = models.TextField(verbose_name="Заметки о посещении")
    photos = models.ImageField(
        upload_to='user_photos/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name="Фотографии с посещения"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Заметка о посещении"
        verbose_name_plural = "Заметки о посещениях"

    def __str__(self):
        return f"{self.user.username} - {self.waypoint.name} ({self.visit_date})"

