from django import template
from users.models import FavoriteWaypoint

register = template.Library()

@register.simple_tag
def is_waypoint_favorite(user, waypoint):
    """Проверяет, добавлена ли точка в избранное пользователем"""
    if not user.is_authenticated:
        return False
    return FavoriteWaypoint.objects.filter(user=user, waypoint=waypoint).exists()