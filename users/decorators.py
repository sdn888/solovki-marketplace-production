from django.http import HttpResponseForbidden
from functools import wraps


def guide_required(function=None):
    """Требует роль гида, эксперта или администратора"""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Требуется авторизация")
            if request.user.role not in ['guide', 'expert_guide', 'admin']:
                return HttpResponseForbidden("Требуется роль гида")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)
    return decorator


def expert_guide_required(function=None):
    """Требует роль гида-эксперта или администратора"""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Требуется авторизация")
            if request.user.role not in ['expert_guide', 'admin']:
                return HttpResponseForbidden("Требуется роль гида-эксперта")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)
    return decorator


def admin_required(function=None):
    """Требует роль администратора"""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Требуется авторизация")
            if request.user.role != 'admin':
                return HttpResponseForbidden("Требуются права администратора")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)
    return decorator