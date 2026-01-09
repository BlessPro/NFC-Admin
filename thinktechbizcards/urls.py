from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("dj-admin/", admin.site.urls),
    path("admin/", include("cards.admin_urls")),
    path("client/", include("cards.client_urls")),
    path("", include("cards.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
