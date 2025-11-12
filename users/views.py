from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from routes.models import Waypoint
from .models import FavoriteWaypoint, VisitNote


@login_required
def favorite_add(request, waypoint_id):
    """Добавление точки в избранное"""
    waypoint = get_object_or_404(Waypoint, id=waypoint_id)

    # Проверяем, не добавлена ли уже точка в избранное
    favorite, created = FavoriteWaypoint.objects.get_or_create(
        user=request.user,
        waypoint=waypoint,
        defaults={'priority': 3}  # Средний приоритет по умолчанию
    )

    if created:
        messages.success(request, f'Точка "{waypoint.name}" добавлена в избранное!')
    else:
        messages.info(request, f'Точка "{waypoint.name}" уже в избранном')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'added' if created else 'already_exists'})

    return redirect('routes:route_detail', pk=waypoint.route.pk)


@login_required
def favorite_remove(request, waypoint_id):
    """Удаление точки из избранного"""
    waypoint = get_object_or_404(Waypoint, id=waypoint_id)

    FavoriteWaypoint.objects.filter(
        user=request.user,
        waypoint=waypoint
    ).delete()

    messages.success(request, f'Точка "{waypoint.name}" удалена из избранного')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'removed'})

    return redirect('routes:route_detail', pk=waypoint.route.pk)


@login_required
def favorite_list(request):
    """Список избранных точек пользователя"""
    favorites = FavoriteWaypoint.objects.filter(user=request.user).select_related('waypoint', 'waypoint__route')

    # Группируем по приоритету для красивого отображения
    favorites_by_priority = {}
    for favorite in favorites:
        priority = favorite.priority
        if priority not in favorites_by_priority:
            favorites_by_priority[priority] = []
        favorites_by_priority[priority].append(favorite)

    return render(request, 'users/favorite_list.html', {
        'favorites_by_priority': favorites_by_priority,
        'favorites': favorites
    })


@login_required
def update_favorite_priority(request, favorite_id):
    """Обновление приоритета избранной точки"""
    if request.method == 'POST':
        favorite = get_object_or_404(FavoriteWaypoint, id=favorite_id, user=request.user)
        new_priority = request.POST.get('priority')

        if new_priority and new_priority.isdigit():
            favorite.priority = int(new_priority)
            favorite.save()
            messages.success(request, 'Приоритет обновлен')

        return redirect('users:favorite_list')
