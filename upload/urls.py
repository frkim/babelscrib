from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='upload_page'),
    path('upload/', views.upload_file, name='upload_file'),
    path('translate/', views.translate_documents, name='translate_documents'),
    path('download/<str:filename>/', views.download_file, name='download_file'),
    path('api/files/', views.list_user_files, name='list_user_files'),
    # Health check endpoints
    path('health/', views.health_check, name='health_check'),
    path('ready/', views.readiness_check, name='readiness_check'),
    # Test endpoints
    path('test-azure-storage/', views.test_azure_storage, name='test_azure_storage'),
    path('test-authentication/', views.test_authentication_config, name='test_authentication_config'),
    # Microsoft authentication test
    path('test-microsoft/', views.test_microsoft, name='test_microsoft'),
    # Debug OAuth URLs (only for troubleshooting)
    path('debug-oauth/', views.debug_oauth_urls, name='debug_oauth_urls'),
]