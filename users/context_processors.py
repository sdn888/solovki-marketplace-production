from .utils import is_guide, is_expert_guide, is_admin, can_create_route

def user_roles(request):
    """Добавляет информацию о ролях пользователя в контекст шаблонов"""
    return {
        'user_can_create_routes': can_create_route(request.user),
        'user_is_guide': is_guide(request.user),
        'user_is_expert_guide': is_expert_guide(request.user),
        'user_is_admin': is_admin(request.user),
    }