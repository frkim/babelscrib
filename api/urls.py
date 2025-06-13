from django.urls import path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from upload.views import upload_file, index as upload_page, translate_documents, download_file, list_user_files, health_check, readiness_check, test_azure_storage

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', upload_page, name='upload_page'),
    path('upload/', upload_file, name='upload_file'),
    path('translate/', translate_documents, name='translate_documents'),
    path('download/<str:filename>/', download_file, name='download_file'),
    path('api/files/', list_user_files, name='list_user_files'),
    # Health check endpoints
    path('health/', health_check, name='health_check'),
    path('ready/', readiness_check, name='readiness_check'),
    # Storage test endpoint
    path('test-azure-storage/', test_azure_storage, name='test_azure_storage'),
]

# Serve static files during development and when DEBUG=True
# WhiteNoise will handle static files in production
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)