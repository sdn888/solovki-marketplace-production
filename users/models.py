from django.contrib.auth.models import AbstractUser
from django.db import models
from routes.models import Waypoint  # Импортируем модель точек маршрута


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('tourist', 'Турист'),
        ('traveler', 'Путешественник'),
        ('guide', 'Гид'),
        ('expert_guide', 'Гид-эксперт'),
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

    subscription_type = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Бесплатный'),
            ('basic', 'Базовый'),
            ('premium', 'Премиум'),
        ],
        default='free',
        verbose_name="Тип подписки"
    )

    subscription_expires = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Подписка действует до"
    )

    # Профиль гида - пока просто связь, модель создадим ниже
    guide_profile = models.OneToOneField(
        'GuideProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user'
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
    @property
    def main_photo(self):
        """Возвращает первое фото для обратной совместимости"""
        return self.images.first()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Заметка о посещении"
        verbose_name_plural = "Заметки о посещениях"

    def __str__(self):
        return f"{self.user.username} - {self.waypoint.name} ({self.visit_date})"

# Добавляем после модели VisitNote

class VisitNoteImage(models.Model):
    visit_note = models.ForeignKey(
        VisitNote,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to='visit_notes/%Y/%m/%d/',
        verbose_name="Фотография"
    )
    caption = models.TextField(
        blank=True,
        verbose_name="Подпись к фото"
    )
    order = models.IntegerField(
        default=0,
        verbose_name="Порядок отображения"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Фотография заметки"
        verbose_name_plural = "Фотографии заметок"
        ordering = ['visit_note', 'order']

    def __str__(self):
        return f"Фото для {self.visit_note}"



# добавим две новые модели: PersonalRoute (сам маршрут) и PersonalRoutePoint (точки в маршруте)

class PersonalRoute(models.Model):
    COLOR_CHOICES = [
        ('#1ABC9C', 'Бирюзовый'),
        ('#3498DB', 'Синий'),
        ('#9B59B6', 'Фиолетовый'),
        ('#E74C3C', 'Красный'),
        ('#F39C12', 'Оранжевый'),
        ('#2ECC71', 'Зеленый'),
        ('#34495E', 'Темно-синий'),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='personal_routes',
        verbose_name="Пользователь"
    )
    title = models.CharField(max_length=200, verbose_name="Название маршрута")
    description = models.TextField(blank=True, verbose_name="Описание")
    color = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES,
        default='#1ABC9C',
        verbose_name="Цвет маршрута"
    )
    is_public = models.BooleanField(default=False, verbose_name="Публичный маршрут")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} (by {self.user.username})"

    class Meta:
        verbose_name = "Персональный маршрут"
        verbose_name_plural = "Персональные маршруты"
        ordering = ['-created_at']

class PersonalRoutePoint(models.Model):
    route = models.ForeignKey(
        PersonalRoute,
        on_delete=models.CASCADE,
        related_name='points'
    )
    waypoint = models.ForeignKey(
        Waypoint,
        on_delete=models.CASCADE,
        verbose_name="Точка маршрута"
    )
    order = models.IntegerField(default=0, verbose_name="Порядок в маршруте")
    notes = models.TextField(blank=True, verbose_name="Заметки для точки")

    class Meta:
        verbose_name = "Точка персонального маршрута"
        verbose_name_plural = "Точки персональных маршрутов"
        ordering = ['route', 'order']
        unique_together = ['route', 'order']

    def __str__(self):
        return f"{self.order}. {self.waypoint.name} (в {self.route.title})"


# Добавляем ПОСЛЕ всех существующих моделей (VisitNote, PersonalRoute, etc.)

class GuideProfile(models.Model):
    """Расширенный профиль для гидов"""
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='guide_profile_rel'
    )

    bio = models.TextField(verbose_name="Биография", blank=True)
    experience_years = models.IntegerField(
        default=0,
        verbose_name="Опыт работы (лет)"
    )
    specialties = models.TextField(
        verbose_name="Специализации",
        help_text="Через запятую",
        blank=True
    )

    # Контактная информация для клиентов
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Контактный телефон"
    )
    contact_email = models.EmailField(
        blank=True,
        verbose_name="Контактный email"
    )

    # Социальные сети
    website = models.URLField(blank=True, verbose_name="Веб-сайт")
    vk_url = models.URLField(blank=True, verbose_name="VK")
    telegram = models.CharField(max_length=100, blank=True, verbose_name="Telegram")

    # Верификация
    is_verified = models.BooleanField(default=False, verbose_name="Верифицирован")
    verification_documents = models.FileField(
        upload_to='guide_documents/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name="Документы для верификации"
    )

    # Рейтинги и статистика
    average_rating = models.FloatField(default=0.0, verbose_name="Средний рейтинг")
    completed_tours = models.IntegerField(default=0, verbose_name="Проведено туров")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Профиль гида: {self.user.username}"

    class Meta:
        verbose_name = "Профиль гида"
        verbose_name_plural = "Профили гидов"