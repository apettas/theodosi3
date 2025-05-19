# pdede_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from proypiresies_app import views as proypiresies_views # <--- ΠΡΟΣΘΕΣΤΕ ΑΥΤΟ

urlpatterns = [
    path('', proypiresies_views.home_view, name='home'), # <--- ΠΡΟΣΘΕΣΤE AYTO
    path('admin/', admin.site.urls),
    path('app/', include('proypiresies_app.urls', namespace='proypiresies_app')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)