from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json
from routes.models import Waypoint
from .models import FavoriteWaypoint, VisitNote, PersonalRoute, PersonalRoutePoint
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from .forms import PersonalRouteForm
from django.db import transaction
from .forms import VisitNoteForm
from django.utils import timezone
from django.db.models import Q


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
    context_object_name = 'personal_routes'  # Измените с 'routes' на 'personal_routes'

    def get_queryset(self):
        return PersonalRoute.objects.filter(user=self.request.user)


class PersonalRouteCreateView(CreateView):
    model = PersonalRoute
    form_class = PersonalRouteForm
    template_name = 'users/personal_route_form.html'
    success_url = reverse_lazy('users:personal_route_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем COLOR_CHOICES в контекст для шаблона
        context['color_choices'] = PersonalRoute.COLOR_CHOICES
        return context


class PersonalRouteUpdateView(UpdateView):
    model = PersonalRoute
    form_class = PersonalRouteForm
    template_name = 'users/personal_route_form.html'
    success_url = reverse_lazy('users:personal_route_list')

    def get_queryset(self):
        return PersonalRoute.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['color_choices'] = PersonalRoute.COLOR_CHOICES
        return context

class PersonalRouteDeleteView(DeleteView):
    model = PersonalRoute
    template_name = 'users/personal_route_confirm_delete.html'
    success_url = reverse_lazy('users:personal_route_list')

    def get_queryset(self):
        return PersonalRoute.objects.filter(user=self.request.user)

class PersonalRouteDetailView(DetailView):
    model = PersonalRoute
    template_name = 'users/personal_route_detail.html'
    context_object_name = 'personal_route'  # ИЗМЕНИЛИ НА personal_route

    def get_queryset(self):
        return PersonalRoute.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем точки маршрута в контекст
        context['points'] = self.object.points.all().select_related('waypoint', 'waypoint__route')
        return context

@login_required
def add_point_to_personal_route(request, route_id, waypoint_id):
    """Добавление точки в персональный маршрут"""
    personal_route = get_object_or_404(PersonalRoute, id=route_id, user=request.user)
    waypoint = get_object_or_404(Waypoint, id=waypoint_id)

    # Определяем следующий порядковый номер
    next_order = personal_route.points.count() + 1

    # Проверяем, не добавлена ли уже эта точка в маршрут
    existing_point = PersonalRoutePoint.objects.filter(
        route=personal_route,
        waypoint=waypoint
    ).first()

    if existing_point:
        messages.info(request, f'Точка "{waypoint.name}" уже есть в маршруте "{personal_route.title}"')
    else:
        PersonalRoutePoint.objects.create(
            route=personal_route,
            waypoint=waypoint,
            order=next_order
        )
        messages.success(request, f'Точка "{waypoint.name}" добавлена в маршрут "{personal_route.title}"')

    # Возвращаем на страницу, откуда пришел запрос
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def remove_point_from_personal_route(request, route_id, point_id):
    """Удаление точки из персонального маршрута"""
    personal_route = get_object_or_404(PersonalRoute, id=route_id, user=request.user)
    point = get_object_or_404(PersonalRoutePoint, id=point_id, route=personal_route)

    if request.method == 'POST':
        point_name = point.waypoint.name
        point.delete()

        # Перенумеровываем оставшиеся точки
        points = personal_route.points.all().order_by('order')
        for index, p in enumerate(points, start=1):
            p.order = index
            p.save()

        messages.success(request, f'Точка "{point_name}" удалена из маршрута "{personal_route.title}"')
        return redirect('users:personal_route_detail', pk=personal_route.id)

    # Если это GET-запрос, показываем страницу подтверждения
    return render(request, 'users/personal_route_point_confirm_delete.html', {
        'point': point,
        'personal_route': personal_route
    })


@login_required
def update_points_order(request, route_id):
    """Обновление порядка точек в персональном маршруте"""
    if request.method == 'POST':
        try:
            personal_route = get_object_or_404(PersonalRoute, id=route_id, user=request.user)
            data = json.loads(request.body)
            order_data = data.get('order', [])

            # Используем транзакцию для атомарности
            with transaction.atomic():
                # Сначала сбрасываем порядок всех точек на временные значения
                points = PersonalRoutePoint.objects.filter(route=personal_route)
                for point in points:
                    point.order = point.order + 10000  # Временное смещение
                    point.save()

                # Теперь устанавливаем новый порядок
                for item in order_data:
                    point_id = item.get('point_id')
                    new_order = item.get('order')

                    point = get_object_or_404(PersonalRoutePoint, id=point_id, route=personal_route)
                    point.order = new_order
                    point.save()

            return JsonResponse({'status': 'success', 'message': 'Порядок точек обновлен'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Метод не разрешен'}, status=405)

class VisitNoteListView(ListView):
    model = VisitNote
    template_name = 'users/visit_notes/visitnote_list.html'
    context_object_name = 'visit_notes'

    def get_queryset(self):
        return VisitNote.objects.filter(user=self.request.user).select_related('waypoint', 'waypoint__route')


class VisitNoteCreateView(CreateView):
    model = VisitNote
    form_class = VisitNoteForm
    template_name = 'users/visit_notes/visitnote_form.html'
    success_url = reverse_lazy('users:visitnote_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        waypoint_id = self.request.GET.get('waypoint_id')
        if waypoint_id:
            try:
                waypoint = Waypoint.objects.get(id=waypoint_id)
                initial['waypoint'] = waypoint
            except Waypoint.DoesNotExist:
                pass
        initial['visit_date'] = timezone.now().date()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        waypoint_id = self.request.GET.get('waypoint_id')
        if waypoint_id:
            try:
                context['preselected_waypoint'] = Waypoint.objects.get(id=waypoint_id)
            except Waypoint.DoesNotExist:
                pass
        return context

    def form_valid(self, form):
        # Проверяем, нет ли уже заметки для этой точки в эту дату
        existing_note = VisitNote.objects.filter(
            user=self.request.user,
            waypoint=form.instance.waypoint,
            visit_date=form.instance.visit_date
        ).first()

        if existing_note and not self.request.POST.get('force_save'):
            # Если заметка уже существует, показываем предупреждение
            context = self.get_context_data(form=form)
            context['existing_note'] = existing_note
            return self.render_to_response(context)

        response = super().form_valid(form)
        messages.success(self.request, f'Заметка о посещении "{form.instance.waypoint.name}" успешно сохранена!')
        return response

class VisitNoteUpdateView(UpdateView):
    model = VisitNote
    form_class = VisitNoteForm
    template_name = 'users/visit_notes/visitnote_form.html'
    success_url = reverse_lazy('users:visitnote_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        return VisitNote.objects.filter(user=self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Заметка о посещении "{form.instance.waypoint.name}" успешно обновлена!')
        return response

class VisitNoteDeleteView(DeleteView):
    model = VisitNote
    template_name = 'users/visit_notes/visitnote_confirm_delete.html'
    success_url = reverse_lazy('users:visitnote_list')

    def get_queryset(self):
        return VisitNote.objects.filter(user=self.request.user)


@login_required
def add_photos_to_visit_note(request, note_id):
    """Добавление дополнительных фото к заметке"""
    visit_note = get_object_or_404(VisitNote, id=note_id, user=request.user)

    if request.method == 'POST' and request.FILES:
        photos = request.FILES.getlist('additional_photos')
        for i, photo in enumerate(photos):
            VisitNoteImage.objects.create(
                visit_note=visit_note,
                image=photo,
                order=visit_note.note_images.count() + i
            )
        messages.success(request, f'Добавлено {len(photos)} фотографий к заметке')
        return redirect('users:visitnote_list')

    return redirect('users:visitnote_list')