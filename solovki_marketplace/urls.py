from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from routes.views import route_list  # добавляем импорт

urlpatterns = [
    path('admin/', admin.site.urls),
    path('routes/', include('routes.urls', namespace='routes')),
    path('users/', include('users.urls', namespace='users')),
    path('', route_list, name='home'),  # главная страница
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
