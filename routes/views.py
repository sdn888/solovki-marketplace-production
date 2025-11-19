from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Route, Waypoint
from users.models import VisitNote


def route_list(request):
    routes = Route.objects.filter(is_active=True).prefetch_related('tips', 'waypoints')
    return render(request, 'routes/route_list.html', {'routes': routes})


def route_detail(request, pk):
    route = get_object_or_404(Route, pk=pk, is_active=True)
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