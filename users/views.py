from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from routes.models import Waypoint
from .models import FavoriteWaypoint, VisitNote, PersonalRoute, PersonalRoutePoint
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy



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

class PersonalRouteListView(ListView):
    model = PersonalRoute
    template_name = 'users/personal_route_list.html'
    context_object_name = 'routes'

    def get_queryset(self):
        return PersonalRoute.objects.filter(user=self.request.user)

class PersonalRouteCreateView(CreateView):
    model = PersonalRoute
    template_name = 'users/personal_route_form.html'
    fields = ['title', 'description', 'color', 'is_public']
    success_url = reverse_lazy('users:personal_route_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class PersonalRouteUpdateView(UpdateView):
    model = PersonalRoute
    template_name = 'users/personal_route_form.html'
    fields = ['title', 'description', 'color', 'is_public']
    success_url = reverse_lazy('users:personal_route_list')

    def get_queryset(self):
        return PersonalRoute.objects.filter(user=self.request.user)

class PersonalRouteDeleteView(DeleteView):
    model = PersonalRoute
    template_name = 'users/personal_route_confirm_delete.html'
    success_url = reverse_lazy('users:personal_route_list')

    def get_queryset(self):
        return PersonalRoute.objects.filter(user=self.request.user)

class PersonalRouteDetailView(DetailView):
    model = PersonalRoute
    template_name = 'users/personal_route_detail.html'
    context_object_name = 'route'

    def get_queryset(self):
        return PersonalRoute.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем точки маршрута в контекст
        context['points'] = self.object.points.all().select_related('waypoint', 'waypoint__route')
        return context

def add_point_to_personal_route(request, route_id, waypoint_id):
    """Добавление точки в персональный маршрут"""
    route = get_object_or_404(PersonalRoute, id=route_id, user=request.user)
    waypoint = get_object_or_404(Waypoint, id=waypoint_id)

    # Определяем следующий порядковый номер
    next_order = route.points.count() + 1

    # Создаем точку в маршруте
    PersonalRoutePoint.objects.create(
        route=route,
        waypoint=waypoint,
        order=next_order
    )

    messages.success(request, f'Точка "{waypoint.name}" добавлена в маршрут "{route.title}"')
    return redirect('routes:route_detail', pk=waypoint.route.pk)

def remove_point_from_personal_route(request, route_id, point_id):
    """Удаление точки из персонального маршрута"""
    route = get_object_or_404(PersonalRoute, id=route_id, user=request.user)
    point = get_object_or_404(PersonalRoutePoint, id=point_id, route=route)

    point.delete()

    # Перенумеровываем оставшиеся точки
    for index, point in enumerate(route.points.all().order_by('order')):
        point.order = index + 1
        point.save()

    messages.success(request, f'Точка удалена из маршрута "{route.title}"')
    return redirect('users:personal_route_detail', pk=route_id)


@login_required
def personal_route_list(request):
    """Список персональных маршрутов пользователя"""
    personal_routes = PersonalRoute.objects.filter(user=request.user)
    return render(request, 'users/personal_route_list.html', {
        'personal_routes': personal_routes
    })


@login_required
def personal_route_create(request):
    """Создание нового персонального маршрута"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        color = request.POST.get('color', '#FF6B6B')
        is_public = request.POST.get('is_public') == 'on'

        if title:
            personal_route = PersonalRoute.objects.create(
                user=request.user,
                title=title,
                description=description,
                color=color,
                is_public=is_public
            )
            messages.success(request, f'Маршрут "{title}" успешно создан!')
            return redirect('users:personal_route_detail', route_id=personal_route.id)
        else:
            messages.error(request, 'Название маршрута обязательно')

    return render(request, 'users/personal_route_form.html')


@login_required
def personal_route_detail(request, route_id):
    """Детальная страница персонального маршрута"""
    personal_route = get_object_or_404(PersonalRoute, id=route_id, user=request.user)
    points = personal_route.points.all().select_related('waypoint', 'waypoint__route')
    return render(request, 'users/personal_route_detail.html', {
        'personal_route': personal_route,
        'points': points
    })


@login_required
def personal_route_edit(request, route_id):
    """Редактирование персонального маршрута"""
    personal_route = get_object_or_404(PersonalRoute, id=route_id, user=request.user)

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        color = request.POST.get('color', '#FF6B6B')
        is_public = request.POST.get('is_public') == 'on'

        if title:
            personal_route.title = title
            personal_route.description = description
            personal_route.color = color
            personal_route.is_public = is_public
            personal_route.save()
            messages.success(request, f'Маршрут "{title}" успешно обновлен!')
            return redirect('users:personal_route_detail', route_id=personal_route.id)
        else:
            messages.error(request, 'Название маршрута обязательно')

    return render(request, 'users/personal_route_form.html', {
        'personal_route': personal_route
    })


@login_required
def personal_route_delete(request, route_id):
    """Удаление персонального маршрута"""
    personal_route = get_object_or_404(PersonalRoute, id=route_id, user=request.user)

    if request.method == 'POST':
        title = personal_route.title
        personal_route.delete()
        messages.success(request, f'Маршрут "{title}" успешно удален!')
        return redirect('users:personal_route_list')

    return render(request, 'users/personal_route_confirm_delete.html', {
        'personal_route': personal_route
    })


@login_required
def add_point_to_personal_route(request, route_id, waypoint_id):
    """Добавление точки в персональный маршрут"""
    personal_route = get_object_or_404(PersonalRoute, id=route_id, user=request.user)
    waypoint = get_object_or_404(Waypoint, id=waypoint_id)

    # Определяем следующий порядковый номер
    next_order = personal_route.points.count() + 1

    # Проверяем, не добавлена ли уже эта точка в маршрут
    if PersonalRoutePoint.objects.filter(route=personal_route, waypoint=waypoint).exists():
        messages.info(request, f'Точка "{waypoint.name}" уже есть в маршруте "{personal_route.title}"')
    else:
        PersonalRoutePoint.objects.create(
            route=personal_route,
            waypoint=waypoint,
            order=next_order
        )
        messages.success(request, f'Точка "{waypoint.name}" добавлена в маршрут "{personal_route.title}"')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})

    # Возвращаем на страницу, откуда пришел запрос
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def remove_point_from_personal_route(request, route_id, point_id):
    """Удаление точки из персонального маршрута"""
    personal_route = get_object_or_404(PersonalRoute, id=route_id, user=request.user)
    point = get_object_or_404(PersonalRoutePoint, id=point_id, route=personal_route)

    if request.method == 'POST':
        point.delete()
        # Перенумеровываем оставшиеся точки
        points = personal_route.points.all().order_by('order')
        for index, p in enumerate(points, start=1):
            p.order = index
            p.save()

        messages.success(request, f'Точка удалена из маршрута "{personal_route.title}"')
        return redirect('users:personal_route_detail', route_id=personal_route.id)

    return render(request, 'users/personal_route_point_confirm_delete.html', {
        'point': point,
        'personal_route': personal_route
    })

