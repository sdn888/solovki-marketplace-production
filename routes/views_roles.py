from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseForbidden

from .models import Route
from .forms import RouteForm
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