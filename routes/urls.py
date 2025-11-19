from django.urls import path
from . import views

app_name = 'routes'

urlpatterns = [
    path('', views.route_list, name='route_list'),
    path('<int:pk>/', views.route_detail, name='route_detail'),
    path('<int:pk>/geojson/', views.route_geojson, name='route_geojson'),
    path('<int:pk>/visit-notes/', views.route_visit_notes, name='route_visit_notes'),
]