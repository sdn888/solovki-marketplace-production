from django.contrib import admin
from django.utils.html import format_html
from .models import Route, Waypoint, WaypointImage, RouteTip, RouteImage
from .forms import RouteForm, WaypointForm

class RouteImageInline(admin.TabularInline):
    model = RouteImage
    extra = 1
    fields = ['image', 'caption', 'order', 'is_primary']


class WaypointImageInline(admin.TabularInline):
    model = WaypointImage
    extra = 3
    fields = ['image', 'caption', 'order', 'is_primary']
    ordering = ['order']


class RouteTipInline(admin.TabularInline):
    model = RouteTip
    extra = 1
    fields = ['title', 'description', 'order']
    ordering = ['order']


class WaypointInline(admin.TabularInline):
    model = Waypoint
    form = WaypointForm
    extra = 1
    fields = ['order', 'name', 'waypoint_type', 'latitude', 'longitude']
    ordering = ['order']
    show_change_link = True


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    form = RouteForm
    list_display = ['title', 'theme', 'transport_type', 'duration_hours', 'price', 'is_active', 'status', 'author']
    list_filter = ['theme', 'transport_type', 'is_active', 'status', 'author']
    search_fields = ['title', 'description']
    inlines = [RouteImageInline, WaypointInline, RouteTipInline]

    # ДОБАВЛЯЕМ ЭТИ ДЕЙСТВИЯ
    actions = ['make_published', 'make_draft', 'make_pending', 'make_archived', 'make_rejected']

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'theme', 'transport_type')
        }),
        ('Детали маршрута', {
            'fields': ('duration_hours', 'price', 'max_participants', 'need_food_supply')
        }),
        ('Геоданные', {
            'fields': ('start_lat', 'start_lon', 'end_lat', 'end_lon'),
        }),
        ('Статус и доступ', {
            'fields': ('is_active', 'status', 'access_level', 'is_premium', 'author')
        }),
    )

    # ДОБАВЛЯЕМ МЕТОДЫ ДЛЯ ДЕЙСТВИЙ
    def make_published(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} маршрут(ов) опубликовано')

    make_published.short_description = "Опубликовать выбранные маршруты"

    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} маршрут(ов) переведено в черновик')

    make_draft.short_description = "Перевести в черновик"

    def make_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} маршрут(ов) отправлено на модерацию')

    make_pending.short_description = "Отправить на модерацию"

    def make_archived(self, request, queryset):
        updated = queryset.update(status='archived')
        self.message_user(request, f'{updated} маршрут(ов) перемещено в архив')

    make_archived.short_description = "Переместить в архив"

    def make_rejected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} маршрут(ов) отклонено')

    make_rejected.short_description = "Отклонить маршруты"


@admin.register(Waypoint)
class WaypointAdmin(admin.ModelAdmin):
    form = WaypointForm
    list_display = ['name', 'route', 'order', 'waypoint_type', 'short_description_preview']
    list_filter = ['waypoint_type', 'route', 'difficulty']
    search_fields = ['name', 'short_description', 'detailed_description', 'history_info']
    ordering = ['route', 'order']
    inlines = [WaypointImageInline]

    def short_description_preview(self, obj):
        if obj.short_description:
            return obj.short_description[:100] + "..." if len(obj.short_description) > 100 else obj.short_description
        return "-"

    short_description_preview.short_description = "Краткое описание"

    fieldsets = (
        ('Основная информация', {
            'fields': ('route', 'order', 'name', 'waypoint_type', 'short_description')
        }),
        ('Подробные описания', {
            'fields': ('detailed_description', 'history_info', 'architecture_info'),
            'description': 'Здесь можно добавить полное описание достопримечательности'
        }),
        ('Особенности посещения', {
            'fields': ('visit_notes', 'path_description', 'best_time_to_visit', 'difficulty'),
            'description': 'Информация о том, как добраться и что учесть при посещении'
        }),
        ('Практическая информация', {
            'fields': ('estimated_stay_minutes', 'has_food', 'has_toilets', 'has_parking',
                       'is_wheelchair_accessible', 'is_optional'),
        }),
        ('Геоданные', {
            'fields': ('latitude', 'longitude', 'altitude')
        }),
    )


@admin.register(WaypointImage)
class WaypointImageAdmin(admin.ModelAdmin):
    list_display = ['waypoint', 'caption_preview', 'order', 'is_primary', 'image_preview']
    list_filter = ['waypoint__route', 'is_primary']
    ordering = ['waypoint', 'order']

    def caption_preview(self, obj):
        if obj.caption:
            return obj.caption[:50] + "..." if len(obj.caption) > 50 else obj.caption
        return "-"

    caption_preview.short_description = "Подпись"

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        return "-"

    image_preview.short_description = "Превью"


@admin.register(RouteImage)
class RouteImageAdmin(admin.ModelAdmin):
    list_display = ['route', 'caption_preview', 'order', 'is_primary', 'image_preview']
    list_filter = ['route', 'is_primary']
    ordering = ['route', 'order']

    def caption_preview(self, obj):
        if obj.caption:
            return obj.caption[:50] + "..." if len(obj.caption) > 50 else obj.caption
        return "-"

    caption_preview.short_description = "Подпись"

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        return "-"

    image_preview.short_description = "Превью"


@admin.register(RouteTip)
class RouteTipAdmin(admin.ModelAdmin):
    list_display = ['route', 'title', 'order']
    list_filter = ['route']
    ordering = ['route', 'order']