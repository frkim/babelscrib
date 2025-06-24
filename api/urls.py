from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Main URL patterns
urlpatterns = [
    path('', include('upload.urls')),
]

# Serve static files during development and when DEBUG=True
# WhiteNoise will handle static files in production
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)