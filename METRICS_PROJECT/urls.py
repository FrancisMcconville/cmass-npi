from django.conf.urls import include, url
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^metrics/', include('metrics.urls', namespace='metrics')),
    url(r'^npi/', include('npi.urls', namespace='npi')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
