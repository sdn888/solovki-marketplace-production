from django.urls import path
from . import views
from . import views_roles


app_name = 'routes'

urlpatterns = [
    path('', views.route_list, name='route_list'),
    path('<int:pk>/', views.route_detail, name='route_detail'),
    path('<int:pk>/geojson/', views.route_geojson, name='route_geojson'),
    path('<int:pk>/visit-notes/', views.route_visit_notes, name='route_visit_notes'),
    path('<int:pk>/export-pdf/', views.route_export_pdf, name='route_export_pdf'),
    path('<int:pk>/export-gpx/', views.route_export_gpx, name='route_export_gpx'),

    # НОВЫЕ URLs для управления маршрутами
    path('create/', views_roles.RouteCreateView.as_view(), name='route_create'),
    path('<int:pk>/edit/', views_roles.RouteUpdateView.as_view(), name='route_update'),
    path('<int:pk>/delete/', views_roles.RouteDeleteView.as_view(), name='route_delete'),
    path('my-routes/', views_roles.UserRoutesListView.as_view(), name='user_routes'),

    # URLs для модерации
    path('moderation/', views_roles.ModerationQueueListView.as_view(), name='moderation_queue'),
    path('<int:pk>/moderate/<str:action>/', views_roles.moderate_route, name='moderate_route'),
]