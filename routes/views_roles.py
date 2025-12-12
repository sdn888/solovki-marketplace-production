from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.db import transaction, models
import json
from django.utils.decorators import method_decorator
import logging

from .models import Route, Waypoint, WaypointImage
from .forms import RouteForm
from .forms_guides import GuideWaypointForm
from users.decorators import guide_required
from users.utils import can_edit_route, can_moderate_route

logger = logging.getLogger(__name__)


# Представление для создания маршрута
@method_decorator([login_required, guide_required], name='dispatch')
class RouteCreateView(CreateView):
    model = Route
    form_class = RouteForm
    template_name = 'routes/route_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Маршрут успешно создан!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('routes:route_detail', kwargs={'pk': self.object.pk})


# Представление для редактирования маршрута
@method_decorator(login_required, name='dispatch')
class RouteUpdateView(UpdateView):
    model = Route
    form_class = RouteForm
    template_name = 'routes/route_form.html'

    def get_queryset(self):
        # Администраторы могут редактировать любые маршруты
        if self.request.user.role == 'admin':
            return Route.objects.all()
        # Гиды могут редактировать только свои маршруты
        return Route.objects.filter(author=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Маршрут успешно обновлен!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('routes:route_detail', kwargs={'pk': self.object.pk})


# Представление для удаления маршрута
@method_decorator(login_required, name='dispatch')
class RouteDeleteView(DeleteView):
    model = Route
    template_name = 'routes/route_confirm_delete.html'
    success_url = reverse_lazy('routes:route_list')

    def get_queryset(self):
        # Администраторы могут удалять любые маршруты
        if self.request.user.role == 'admin':
            return Route.objects.all()
        # Гиды могут удалять только свои маршруты
        return Route.objects.filter(author=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Маршрут успешно удален!')
        return super().delete(request, *args, **kwargs)


# Представление для списка маршрутов пользователя
@method_decorator([login_required, guide_required], name='dispatch')
class UserRoutesListView(ListView):
    model = Route
    template_name = 'routes/user_route_list.html'
    context_object_name = 'routes'

    def get_queryset(self):
        return Route.objects.filter(author=self.request.user).order_by('-created_at')


# Функция для модерации маршрутов
@login_required
def moderate_route(request, pk, action):
    """Модерация маршрута (одобрение/отклонение)"""
    if not can_moderate_route(request.user):
        return HttpResponseForbidden("У вас нет прав для модерации")

    route = get_object_or_404(Route, pk=pk)

    if action == 'approve':
        route.status = 'published'
        route.moderated_by = request.user
        route.moderation_notes = 'Одобрено модератором'
        messages.success(request, f'Маршрут "{route.title}" одобрен и опубликован')
    elif action == 'reject':
        route.status = 'rejected'
        route.moderated_by = request.user
        messages.success(request, f'Маршрут "{route.title}" отклонен')
    elif action == 'archive':
        route.status = 'archived'
        messages.success(request, f'Маршрут "{route.title}" перемещен в архив')

    route.save()
    return redirect('routes:moderation_queue')


# Представление для очереди модерации
@method_decorator([login_required], name='dispatch')
class ModerationQueueListView(ListView):
    model = Route
    template_name = 'routes/moderation_queue.html'
    context_object_name = 'routes'

    def get_queryset(self):
        if not can_moderate_route(self.request.user):
            return Route.objects.none()
        return Route.objects.filter(status='pending').order_by('created_at')


# Управление точками маршрута
@login_required
def manage_waypoints(request, pk):
    """Страница управления точками маршрута"""
    route = get_object_or_404(Route, pk=pk)

    # Проверяем права доступа
    if not can_edit_route(request.user, route):
        return HttpResponseForbidden("У вас нет прав для управления точками этого маршрута")

    waypoints = route.waypoints.all().order_by('order')

    return render(request, 'routes/manage_waypoints.html', {
        'route': route,
        'waypoints': waypoints,
    })


# Создание точки маршрута
@method_decorator([login_required], name='dispatch')
class WaypointCreateView(CreateView):
    model = Waypoint
    form_class = GuideWaypointForm
    template_name = 'routes/waypoint_form.html'

    def get_route(self):
        return get_object_or_404(Route, pk=self.kwargs['route_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['route'] = self.get_route()
        return context

    # ПЕРЕОПРЕДЕЛЯЕМ get_form, а не get_form_kwargs
    def get_form(self, form_class=None):
        """Создаем форму с передачей route"""
        form = super().get_form(form_class)
        route = self.get_route()

        # Передаем route в форму через атрибут
        if hasattr(form, 'route'):
            form.route = route

        # Устанавливаем начальное значение для order
        if route and not form.instance.pk:
            max_order = route.waypoints.aggregate(models.Max('order'))['order__max']
            form.fields['order'].initial = (max_order or 0) + 1

        return form

    def form_valid(self, form):
        route = self.get_route()
        form.instance.route = route

        # Если order не указан, устанавливаем автоматически
        if not form.cleaned_data.get('order'):
            max_order = route.waypoints.aggregate(models.Max('order'))['order__max']
            form.instance.order = (max_order or 0) + 1

        try:
            response = super().form_valid(form)
            print("✅ Точка успешно создана!")
            messages.success(self.request, '✅ Точка маршрута успешно создана!')
            return response
        except Exception as e:
            print(f"❌ Ошибка при сохранении: {e}")
            messages.error(self.request, f'❌ Ошибка при создании точки: {e}')
            return self.form_invalid(form)

    # УБИРАЕМ метод get_form_kwargs, т.к. теперь используем get_form


# Редактирование точки маршрута
@method_decorator([login_required], name='dispatch')
class WaypointUpdateView(UpdateView):
    model = Waypoint
    form_class = GuideWaypointForm
    template_name = 'routes/waypoint_form.html'

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Waypoint.objects.all()
        return Waypoint.objects.filter(route__author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['route'] = self.object.route
        return context

    def get_form(self, form_class=None):
        """Создаем форму с передачей route"""
        form = super().get_form(form_class)

        # Передаем route в форму через атрибут
        if hasattr(form, 'route'):
            form.route = self.object.route

        return form

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            print("✅ Точка успешно обновлена!")
            messages.success(self.request, '✅ Точка маршрута успешно обновлена!')
            return response
        except Exception as e:
            print(f"❌ Ошибка при обновлении: {e}")
            messages.error(self.request, f'❌ Ошибка при обновлении точки: {e}')
            return self.form_invalid(form)

    # УБИРАЕМ метод get_form_kwargs


# Удаление точки маршрута
@method_decorator([login_required], name='dispatch')
class WaypointDeleteView(DeleteView):
    model = Waypoint
    template_name = 'routes/waypoint_confirm_delete.html'

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Waypoint.objects.all()
        return Waypoint.objects.filter(route__author=self.request.user)

    def delete(self, request, *args, **kwargs):
        waypoint = self.get_object()
        route_pk = waypoint.route.pk
        messages.success(request, f'✅ Точка "{waypoint.name}" успешно удалена!')
        response = super().delete(request, *args, **kwargs)
        # После удаления перенумеровываем оставшиеся точки
        waypoints = Waypoint.objects.filter(route=waypoint.route).order_by('order')
        for index, wp in enumerate(waypoints, start=1):
            wp.order = index
            wp.save()
        return response

    def get_success_url(self):
        return reverse_lazy('routes:manage_waypoints', kwargs={'pk': self.object.route.pk})


# Обновление порядка точек (Drag & Drop)
@login_required
def update_waypoints_order(request, route_id):
    """Обновление порядка точек маршрута через Drag & Drop"""
    if request.method == 'POST':
        try:
            route = get_object_or_404(Route, id=route_id)

            # Проверяем права доступа
            if not can_edit_route(request.user, route):
                return JsonResponse({'status': 'error', 'message': 'Нет прав доступа'}, status=403)

            print("=== ДЕБАГ ОБНОВЛЕНИЯ ПОРЯДКА ===")
            print(f"Пользователь: {request.user.username}")
            print(f"Маршрут: {route.title} (ID: {route.id})")

            data = json.loads(request.body)
            order_data = data.get('order', [])
            print(f"Данные порядка: {order_data}")

            with transaction.atomic():

                # Используем временное смещение чтобы избежать конфликтов
                temp_offset = 10000

                # Сначала устанавливаем временные порядки
                for item in order_data:
                    waypoint_id = item.get('waypoint_id')
                    waypoint = get_object_or_404(Waypoint, id=waypoint_id, route=route)
                    waypoint.order = temp_offset + waypoint_id
                    waypoint.save()

                # Затем устанавливаем финальные порядки
                for item in order_data:
                    waypoint_id = item.get('waypoint_id')
                    new_order = item.get('order')
                    waypoint = get_object_or_404(Waypoint, id=waypoint_id, route=route)
                    waypoint.order = new_order
                    waypoint.save()

            print("✅ Порядок успешно обновлен!")
            return JsonResponse({'status': 'success', 'message': 'Порядок точек обновлен'})

        except Exception as e:
            print(f"❌ Ошибка при обновлении порядка: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Метод не разрешен'}, status=405)


@ensure_csrf_cookie
@login_required
def manage_waypoints(request, pk):
    """Страница управления точками маршрута"""
    route = get_object_or_404(Route, pk=pk)

    # Проверяем права доступа
    if not can_edit_route(request.user, route):
        return HttpResponseForbidden("У вас нет прав для управления точками этого маршрута")

    waypoints = route.waypoints.all().order_by('order')

    return render(request, 'routes/manage_waypoints.html', {
        'route': route,
        'waypoints': waypoints,
    })


@login_required
def copy_waypoint_to_route(request, route_id, waypoint_id):
    """Копирование точки в другой маршрут"""

    # Проверяем метод запроса
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Метод не разрешен'}, status=405)

    try:
        target_route = get_object_or_404(Route, pk=route_id)
        source_waypoint = get_object_or_404(Waypoint, pk=waypoint_id)

        # Проверяем права: можно копировать из своих маршрутов или опубликованных
        can_copy = (
                source_waypoint.route.author == request.user or
                source_waypoint.route.status == 'published' or
                request.user.role == 'admin'
        )

        if not can_copy:
            return JsonResponse({'status': 'error', 'message': 'У вас нет прав для копирования этой точки'}, status=403)

        # Получаем параметры из запроса (AJAX)
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                copy_images = data.get('copy_images', True)
            else:
                copy_images = request.POST.get('copy_images', 'true').lower() == 'true'
        except (json.JSONDecodeError, KeyError):
            copy_images = True  # По умолчанию копируем изображения

        # Вычисляем порядок (в конец маршрута)
        max_order = target_route.waypoints.aggregate(models.Max('order'))['order__max']
        new_order = (max_order or 0) + 1

        # Создаем копию точки
        new_waypoint = Waypoint.objects.create(
            route=target_route,
            name=f"{source_waypoint.name} (копия)",
            short_description=source_waypoint.short_description,
            detailed_description=source_waypoint.detailed_description,
            history_info=source_waypoint.history_info,
            architecture_info=source_waypoint.architecture_info,
            visit_notes=source_waypoint.visit_notes,
            path_description=source_waypoint.path_description,
            best_time_to_visit=source_waypoint.best_time_to_visit,
            difficulty=source_waypoint.difficulty,
            estimated_stay_minutes=source_waypoint.estimated_stay_minutes,
            has_food=source_waypoint.has_food,
            has_toilets=source_waypoint.has_toilets,
            has_parking=source_waypoint.has_parking,
            is_wheelchair_accessible=source_waypoint.is_wheelchair_accessible,
            is_optional=source_waypoint.is_optional,
            waypoint_type=source_waypoint.waypoint_type,
            latitude=source_waypoint.latitude,
            longitude=source_waypoint.longitude,
            altitude=source_waypoint.altitude,
            order=new_order
        )

        # Копируем изображения если нужно
        images_copied = 0
        if copy_images:
            for image in source_waypoint.images.all():
                WaypointImage.objects.create(
                    waypoint=new_waypoint,
                    image=image.image,
                    caption=image.caption,
                    order=image.order,
                    is_primary=image.is_primary
                )
                images_copied += 1

        # Логируем успешное копирование
        logger.info(
            f"Пользователь {request.user.username} скопировал точку {source_waypoint.id} в маршрут {target_route.id}")

        # Для AJAX запросов возвращаем JSON
        return JsonResponse({
            'status': 'success',
            'message': f'Точка "{source_waypoint.name}" успешно скопирована в маршрут "{target_route.title}"',
            'new_waypoint_id': new_waypoint.id,
            'images_copied': images_copied,
            'redirect_url': reverse_lazy('routes:manage_waypoints', kwargs={'pk': target_route.pk})
        })

    except Exception as e:
        logger.error(f"Ошибка при копировании точки: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при копировании точки: {str(e)}'
        }, status=500)


@login_required
def user_routes_api(request):
    """API для получения списка маршрутов пользователя"""
    try:
        # Включаем все маршруты пользователя, не только не черновики
        routes = Route.objects.filter(author=request.user)

        routes_data = []
        for route in routes:
            routes_data.append({
                'id': route.id,
                'title': route.title,
                'theme_display': route.get_theme_display(),
                'points_count': route.waypoints.count(),
                'status': route.status,
                'is_active': route.is_active,
                'status_display': route.get_status_display()
            })

        return JsonResponse(routes_data, safe=False)
    except Exception as e:
        logger.error(f"Ошибка в user_routes_api: {e}")
        return JsonResponse({'error': str(e)}, status=500, safe=False)