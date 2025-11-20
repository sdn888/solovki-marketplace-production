from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from .models import Route, Waypoint
from users.models import VisitNote
from .export_utils import generate_route_pdf, generate_route_gpx
from users.utils import is_guide, can_create_route


def route_list(request):
    routes = Route.objects.filter(is_active=True).prefetch_related('tips', 'waypoints')

    # ДОБАВЛЯЕМ базовую фильтрацию по статусу
    routes = routes.filter(status='published')

    return render(request, 'routes/route_list.html', {'routes': routes})


def route_detail(request, pk):
    route = get_object_or_404(Route, pk=pk, is_active=True)

    # ДОБАВЛЯЕМ проверку статуса маршрута
    if route.status != 'published':
        # Проверяем права доступа для неопубликованных маршрутов
        if not request.user.is_authenticated or (request.user != route.author and not request.user.is_staff):
            return HttpResponseForbidden("Маршрут не доступен для просмотра")

    waypoints = route.waypoints.all().order_by('order').prefetch_related('images')
    tips = route.tips.all().order_by('order')

    # Подсчитываем количество отзывов для этого маршрута
    visit_notes_count = VisitNote.objects.filter(
        waypoint__route=route
    ).count()

    # Получаем последние отзывы
    recent_visit_notes = VisitNote.objects.filter(
        waypoint__route=route
    ).select_related('user', 'waypoint').order_by('-created_at')[:5]

    return render(request, 'routes/route_detail.html', {
        'route': route,
        'waypoints': waypoints,
        'tips': tips,
        'visit_notes_count': visit_notes_count,
        'recent_visit_notes': recent_visit_notes
    })

def route_geojson(request, pk):
    route = get_object_or_404(Route, pk=pk)
    waypoints = route.waypoints.all().order_by('order')

    features = []

    # Добавляем точки маршрута
    for waypoint in waypoints:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [waypoint.longitude, waypoint.latitude]
            },
            "properties": {
                "name": waypoint.name,
                "type": waypoint.waypoint_type,
                "order": waypoint.order,
                "description": waypoint.description,
                "stay_minutes": waypoint.estimated_stay_minutes
            }
        })

    # Добавляем линию маршрута (если есть координаты)
    if waypoints.count() > 1:
        coordinates = [[wp.longitude, wp.latitude] for wp in waypoints]
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            },
            "properties": {
                "name": f"Маршрут: {route.title}",
                "color": "#3388ff",
                "weight": 4
            }
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    return JsonResponse(geojson)

def route_visit_notes(request, pk):
    """Страница со всеми отзывами по маршруту"""
    route = get_object_or_404(Route, pk=pk, is_active=True)
    visit_notes = VisitNote.objects.filter(
        waypoint__route=route
    ).select_related('user', 'waypoint').order_by('-created_at')

    return render(request, 'routes/route_visit_notes.html', {
        'route': route,
        'visit_notes': visit_notes
    })


def route_export_pdf(request, pk):
    """Экспорт маршрута в PDF"""
    route = get_object_or_404(Route, pk=pk, is_active=True)
    waypoints = route.waypoints.all().order_by('order').prefetch_related('images')

    # Генерируем PDF
    pdf_buffer = generate_route_pdf(route, waypoints)

    # Создаем HTTP-ответ
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{route.title}_маршрут.pdf"'
    return response


def route_export_gpx(request, pk):
    """Экспорт маршрута в GPX"""
    route = get_object_or_404(Route, pk=pk, is_active=True)
    waypoints = route.waypoints.all().order_by('order')

    # Генерируем GPX
    gpx_content = generate_route_gpx(route, waypoints)

    # Создаем HTTP-ответ
    response = HttpResponse(gpx_content, content_type='application/gpx+xml')
    response['Content-Disposition'] = f'attachment; filename="{route.title}.gpx"'
    return response