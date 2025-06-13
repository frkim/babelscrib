from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

# Non-i18n URLs (for admin and API endpoints that don't need translation)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # Language switching URLs
]

# i18n URLs (for user-facing pages that need translation)
urlpatterns += i18n_patterns(
    path('', include('upload.urls')),
    prefix_default_language=False,  # Don't add language prefix for default language
)

# Serve static files during development and when DEBUG=True
# WhiteNoise will handle static files in production
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)