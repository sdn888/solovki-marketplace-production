from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, FavoriteWaypoint, VisitNote, PersonalRoute, PersonalRoutePoint


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'first_name', 'last_name', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')

    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('role', 'phone', 'avatar', 'bio')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('role', 'phone', 'avatar', 'bio')
        }),
    )

from django.contrib import admin
from .models import CustomUser, FavoriteWaypoint, VisitNote

# ... существующий код CustomUserAdmin ...

@admin.register(FavoriteWaypoint)
class FavoriteWaypointAdmin(admin.ModelAdmin):
    list_display = ['user', 'waypoint', 'priority', 'planned_visit_date', 'created_at']
    list_filter = ['priority', 'planned_visit_date', 'created_at']
    search_fields = ['user__username', 'waypoint__name', 'personal_notes']
    ordering = ['-created_at']

@admin.register(VisitNote)
class VisitNoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'waypoint', 'visit_date', 'rating', 'created_at']
    list_filter = ['rating', 'visit_date', 'created_at']
    search_fields = ['user__username', 'waypoint__name', 'notes']
    ordering = ['-visit_date']

# новые модели для персональных маршрутов
@admin.register(PersonalRoute)
class PersonalRouteAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'color', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at', 'color']
    search_fields = ['title', 'description', 'user__username']
    ordering = ['-created_at']

@admin.register(PersonalRoutePoint)
class PersonalRoutePointAdmin(admin.ModelAdmin):
    list_display = ['route', 'waypoint', 'order']
    list_filter = ['route', 'route__user']
    search_fields = ['route__title', 'waypoint__name']
    ordering = ['route', 'order']

