from django.urls import path
from . import views
from .views import (PersonalRouteListView, PersonalRouteCreateView,
                   PersonalRouteUpdateView, PersonalRouteDeleteView,
                   PersonalRouteDetailView, add_point_to_personal_route,
                   remove_point_from_personal_route, update_points_order)

app_name = 'users'

urlpatterns = [
    path('favorites/', views.favorite_list, name='favorite_list'),
    path('favorites/add/<int:waypoint_id>/', views.favorite_add, name='favorite_add'),
    path('favorites/remove/<int:waypoint_id>/', views.favorite_remove, name='favorite_remove'),
    path('favorites/update-priority/<int:favorite_id>/', views.update_favorite_priority, name='update_favorite_priority'),
    path('personal-routes/', PersonalRouteListView.as_view(), name='personal_route_list'),
    path('personal-routes/create/', PersonalRouteCreateView.as_view(), name='personal_route_create'),
    path('personal-routes/<int:pk>/edit/', PersonalRouteUpdateView.as_view(), name='personal_route_update'),
    path('personal-routes/<int:pk>/delete/', PersonalRouteDeleteView.as_view(), name='personal_route_delete'),
    path('personal-routes/<int:pk>/', PersonalRouteDetailView.as_view(), name='personal_route_detail'),
    path('personal-routes/<int:route_id>/add-point/<int:waypoint_id>/', add_point_to_personal_route,
         name='add_point_to_personal_route'),
    path('personal-routes/<int:route_id>/remove-point/<int:point_id>/', remove_point_from_personal_route,
         name='remove_point_from_personal_route'),
    path('personal-routes/<int:route_id>/update-order/', update_points_order, name='update_points_order'),
]
