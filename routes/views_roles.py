from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.db import transaction, models  # ← ДОБАВЛЯЕМ models здесь!
from django.db import transaction
import json
from django.utils.decorators import method_decorator

from .models import Route, Waypoint
from .forms import RouteForm, WaypointForm
from users.decorators import guide_required
from users.utils import can_edit_route, can_moderate_route


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
    form_class = WaypointForm
    template_name = 'routes/waypoint_form.html'

    def get_route(self):
        return get_object_or_404(Route, pk=self.kwargs['route_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['route'] = self.get_route()
        return context

    def form_valid(self, form):
        route = self.get_route()
        form.instance.route = route

        # УЛУЧШАЕМ ЛОГИКУ УСТАНОВКИ ПОРЯДКА
        # Получаем максимальный порядок среди существующих точек
        max_order = route.waypoints.aggregate(models.Max('order'))['order__max']
        # Устанавливаем следующий порядковый номер
        form.instance.order = (max_order or 0) + 1

        # ДОБАВЛЯЕМ ОТЛАДОЧНУЮ ИНФОРМАЦИЮ
        print("=== ДЕБАГ СОЗДАНИЯ ТОЧКИ ===")
        print(f"Маршрут: {route.title} (ID: {route.id})")
        print(f"Текущий максимальный порядок: {max_order}")
        print(f"Новый порядок: {form.instance.order}")
        print(f"Данные формы: {form.cleaned_data}")

        try:
            response = super().form_valid(form)
            print("✅ Точка успешно создана!")
            messages.success(self.request, '✅ Точка маршрута успешно создана!')
            return response
        except Exception as e:
            print(f"❌ Ошибка при сохранении: {e}")
            messages.error(self.request, f'❌ Ошибка при создании точки: {e}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        # ДОБАВЛЯЕМ ОТЛАДОЧНУЮ ИНФОРМАЦИЮ ПРИ ОШИБКАХ
        print("=== ДЕБАГ ОШИБКИ ФОРМЫ ===")
        print(f"Ошибки формы: {form.errors}")
        print(f"Данные формы: {form.data}")
        messages.error(self.request, '❌ Проверьте правильность заполнения формы')
        return super().form_invalid(form)


    def get_success_url(self):
        return reverse_lazy('routes:manage_waypoints', kwargs={'pk': self.kwargs['route_id']})


# Редактирование точки маршрута
@method_decorator([login_required], name='dispatch')
class WaypointUpdateView(UpdateView):
    model = Waypoint
    form_class = WaypointForm
    template_name = 'routes/waypoint_form.html'

    def get_queryset(self):
        # Администраторы могут редактировать любые точки, авторы - только своих маршрутов
        if self.request.user.role == 'admin':
            return Waypoint.objects.all()
        return Waypoint.objects.filter(route__author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['route'] = self.object.route
        return context

    def form_valid(self, form):
        # ДОБАВЛЯЕМ ОТЛАДОЧНУЮ ИНФОРМАЦИЮ ДЛЯ РЕДАКТИРОВАНИЯ
        print("=== ДЕБАГ РЕДАКТИРОВАНИЯ ТОЧКИ ===")
        print(f"Точка: {self.object.name} (ID: {self.object.id})")
        print(f"Данные формы: {form.cleaned_data}")

        try:
            response = super().form_valid(form)
            print("✅ Точка успешно обновлена!")
            messages.success(self.request, '✅ Точка маршрута успешно обновлена!')
            return response
        except Exception as e:
            print(f"❌ Ошибка при обновлении: {e}")
            messages.error(self.request, f'❌ Ошибка при обновлении точки: {e}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        print("=== ДЕБАГ ОШИБКИ ФОРМЫ (РЕДАКТИРОВАНИЕ) ===")
        print(f"Ошибки формы: {form.errors}")
        messages.error(self.request, '❌ Проверьте правильность заполнения формы')
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('routes:manage_waypoints', kwargs={'pk': self.object.route.pk})


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

            # ДОБАВЛЯЕМ ОТЛАДОЧНУЮ ИНФОРМАЦИЮ
            print("=== ДЕБАГ ОБНОВЛЕНИЯ ПОРЯДКА ===")
            print(f"Пользователь: {request.user.username}")
            print(f"Маршрут: {route.title} (ID: {route.id})")

            data = json.loads(request.body)
            order_data = data.get('order', [])
            print(f"Данные порядка: {order_data}")

            with transaction.atomic():
                # Устанавливаем новый порядок
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
