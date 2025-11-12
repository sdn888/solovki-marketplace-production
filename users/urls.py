from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('favorites/', views.favorite_list, name='favorite_list'),
    path('favorites/add/<int:waypoint_id>/', views.favorite_add, name='favorite_add'),
    path('favorites/remove/<int:waypoint_id>/', views.favorite_remove, name='favorite_remove'),
    path('favorites/update-priority/<int:favorite_id>/', views.update_favorite_priority, name='update_favorite_priority'),
]
