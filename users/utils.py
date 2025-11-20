from .models import CustomUser


def is_guide(user):
    """Проверяет, является ли пользователь гидом (guide, expert_guide или admin)"""
    return user.is_authenticated and user.role in ['guide', 'expert_guide', 'admin']


def is_expert_guide(user):
    """Проверяет, является ли пользователь экспертом-гидом или администратором"""
    return user.is_authenticated and user.role in ['expert_guide', 'admin']


def is_admin(user):
    """Проверяет, является ли пользователь администратором"""
    return user.is_authenticated and user.role == 'admin'


def can_create_route(user):
    """Может ли пользователь создавать маршруты"""
    return is_guide(user)


def can_edit_route(user, route):
    """Может ли пользователь редактировать маршрут"""
    if not user.is_authenticated:
        return False
    return user == route.author or is_admin(user)


def can_moderate_route(user):
    """Может ли пользователь модерировать маршруты"""
    return is_admin(user) or is_expert_guide(user)


def get_user_role_display(user):
    """Возвращает читаемое название роли пользователя"""
    if not user.is_authenticated:
        return "Неавторизованный"

    role_dict = dict(CustomUser.ROLE_CHOICES)
    return role_dict.get(user.role, "Неизвестная роль")