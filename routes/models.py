from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Route(models.Model):
    THEME_CHOICES = [
        ('historical', 'Исторический'),
        ('religious', 'Религиозный'),
        ('nature', 'Природоведческий'),
        ('mixed', 'Смешанный'),
    ]

    TRANSPORT_CHOICES = [
        ('foot', 'Пеший'),
        ('bike', 'Велосипед'),
        ('car', 'Автомобиль'),
        ('boat', 'Лодка'),
        ('mixed', 'Смешанный'),
    ]

    # Основная информация
    title = models.CharField(max_length=200, verbose_name="Название маршрута")
    description = models.TextField(verbose_name="Описание маршрута")
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, verbose_name="Тематика")
    transport_type = models.CharField(max_length=20, choices=TRANSPORT_CHOICES, verbose_name="Тип транспорта")
    duration_hours = models.FloatField(
        verbose_name="Длительность (часов)",
        validators=[MinValueValidator(0.5), MaxValueValidator(24)]
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена",
        null=True,
        blank=True
    )
    need_food_supply = models.BooleanField(default=False, verbose_name="Нужен запас еды")
    max_participants = models.IntegerField(
        default=10,
        verbose_name="Максимум участников",
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    # Геоданные маршрута
    start_lat = models.FloatField(verbose_name="Широта старта", null=True, blank=True)
    start_lon = models.FloatField(verbose_name="Долгота старта", null=True, blank=True)
    end_lat = models.FloatField(verbose_name="Широта финиша", null=True, blank=True)
    end_lon = models.FloatField(verbose_name="Долгота финиша", null=True, blank=True)

    def get_gallery_images(self):
        """
        Возвращает первые 4 изображения маршрута или точек маршрута
        """
        images = []

        # Сначала берем изображения самого маршрута
        route_images = self.route_images.all()
        if route_images:
            for image in route_images[:4]:
                images.append(image)
        else:
            # Если нет изображений маршрута, берем из точек маршрута
            for waypoint in self.waypoints.all():
                for image in waypoint.images.all()[:4 - len(images)]:
                    images.append(image)
                if len(images) >= 4:
                    break

        return images

    @property
    def has_parking(self):
        """Есть ли парковка в точках маршрута"""
        return self.waypoints.filter(has_parking=True).exists()

    @property
    def is_wheelchair_accessible(self):
        """Доступен ли маршрут для инвалидных колясок"""
        return self.waypoints.filter(is_wheelchair_accessible=True).exists()

    @property
    def is_popular(self):
        """Популярный маршрут (можно настроить свою логику)"""
        # Например, если у маршрута больше 3 точек или он исторический
        return self.waypoints.count() > 3 or self.theme == 'historical'

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Маршрут"
        verbose_name_plural = "Маршруты"

    static_map_image = models.ImageField(
        upload_to='route_maps/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name="Статическое изображение карты маршрута",
        help_text="Изображение карты маршрута для экспорта в PDF"
    )

class Waypoint(models.Model):
    WAYPOINT_TYPES = [
        ('attraction', 'Достопримечательность'),
        ('food', 'Точка питания'),
        ('info', 'Информационная точка'),
        ('view', 'Смотровая площадка'),
        ('start', 'Старт'),
        ('end', 'Финиш'),
        ('break', 'Место отдыха'),
        ('shrine', 'Святыня, храм'),
        ('skete', 'Скит'),
        ('museum', 'Музей'),
        ('nature', 'Природа'),
    ]

    DIFFICULTY_CHOICES = [
        ('easy', 'Лёгкий'),
        ('moderate', 'Средний'),
        ('hard', 'Сложный'),
    ]

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='waypoints')
    name = models.CharField(max_length=200, verbose_name="Название точки")

    # ОПИСАНИЯ ТОЧКИ - расширенные поля
    short_description = models.TextField(
        verbose_name="Краткое описание точки",
        blank=True,
        help_text="Краткое описание для карточек и списков (до 1000 символов)"
    )
    detailed_description = models.TextField(
        verbose_name="Подробное описание",
        blank=True,
        help_text="Полное описание достопримечательности, её особенностей и значимости"
    )
    history_info = models.TextField(
        verbose_name="Историческая справка",
        blank=True,
        help_text="Исторические факты, даты строительства, значимые события"
    )
    architecture_info = models.TextField(
        verbose_name="Архитектура и особенности",
        blank=True,
        help_text="Описание архитектурных особенностей, стиля, материалов"
    )

    # ОСОБЕННОСТИ ПОСЕЩЕНИЯ
    visit_notes = models.TextField(
        verbose_name="Особенности посещения",
        blank=True,
        help_text="Рекомендации по времени посещения, что взять с собой, особенности поведения"
    )
    path_description = models.TextField(
        verbose_name="Описание пути",
        blank=True,
        help_text="Как добраться до точки, особенности маршрута, сложности пути"
    )
    best_time_to_visit = models.TextField(
        verbose_name="Лучшее время для посещения",
        blank=True,
        help_text="Рекомендуемое время суток, сезон, погодные условия"
    )

    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        verbose_name="Сложность посещения",
        default='easy'
    )

    # Практическая информация
    estimated_stay_minutes = models.IntegerField(
        default=0,
        verbose_name="Рекомендуемое время на посещение (минут)",
        validators=[MinValueValidator(0), MaxValueValidator(480)]
    )
    has_food = models.BooleanField(default=False, verbose_name="Есть питание")
    has_toilets = models.BooleanField(default=False, verbose_name="Есть туалеты")
    has_parking = models.BooleanField(default=False, verbose_name="Есть парковка")
    is_wheelchair_accessible = models.BooleanField(default=False, verbose_name="Доступно для инвалидов")
    is_optional = models.BooleanField(default=False, verbose_name="Опциональная точка")

    # Геоданные
    order = models.IntegerField(verbose_name="Порядковый номер в маршруте")
    waypoint_type = models.CharField(max_length=20, choices=WAYPOINT_TYPES, verbose_name="Тип точки")
    latitude = models.FloatField(verbose_name="Широта")
    longitude = models.FloatField(verbose_name="Долгота")
    altitude = models.IntegerField(null=True, blank=True, verbose_name="Высота над уровнем моря (м)")

    def __str__(self):
        return f"{self.order}. {self.name} ({self.get_waypoint_type_display()})"

    class Meta:
        ordering = ['route', 'order']
        verbose_name = "Точка маршрута"
        verbose_name_plural = "Точки маршрута"
        unique_together = ['route', 'order']


class WaypointImage(models.Model):
    waypoint = models.ForeignKey(Waypoint, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(
        upload_to='waypoints/%Y/%m/%d/',
        verbose_name="Изображение",
        help_text="Рекомендуемый размер: 1200x800px"
    )
    caption = models.TextField(
        verbose_name="Подпись к фото",
        blank=True,
        help_text="Подробное описание фотографии"
    )
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")
    is_primary = models.BooleanField(default=False, verbose_name="Основное фото")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['waypoint', 'order', 'is_primary']
        verbose_name = "Изображение точки"
        verbose_name_plural = "Изображения точек"

    def __str__(self):
        return f"Фото: {self.waypoint.name}"


class RouteTip(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='tips')
    title = models.CharField(max_length=200, verbose_name="Заголовок совета")
    description = models.TextField(verbose_name="Описание совета")
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")

    class Meta:
        ordering = ['route', 'order']
        verbose_name = "Совет по маршруту"
        verbose_name_plural = "Советы по маршруту"

    def __str__(self):
        return self.title


class RouteImage(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='route_images')
    image = models.ImageField(
        upload_to='routes/%Y/%m/%d/',
        verbose_name="Изображение маршрута",
        help_text="Рекомендуемый размер: 1200x800px"
    )
    caption = models.TextField(
        verbose_name="Подпись к фото",
        blank=True,
        help_text="Описание фотографии для главной страницы"
    )
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")
    is_primary = models.BooleanField(default=False, verbose_name="Основное фото")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['route', 'order', 'is_primary']
        verbose_name = "Изображение маршрута"
        verbose_name_plural = "Изображения маршрутов"

    def __str__(self):
        return f"Фото маршрута: {self.route.title}"