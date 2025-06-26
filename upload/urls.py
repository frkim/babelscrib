from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='upload_page'),
    path('upload/', views.upload_file, name='upload_file'),
    path('translate/', views.translate_documents, name='translate_documents'),
    path('download/<str:filename>/', views.download_file, name='download_file'),
    path('delete-translated/', views.delete_translated_documents, name='delete_translated_documents'),
    path('delete-individual/<str:filename>/', views.delete_individual_translated_document, name='delete_individual_translated_document'),
    path('api/files/', views.list_user_files, name='list_user_files'),
    path('api/cleanup-sessions/', views.cleanup_sessions, name='cleanup_sessions'),
    # Debug endpoints
    path('debug/user-files/', views.debug_user_files, name='debug_user_files'),
    # Health check endpoints
    path('health/', views.health_check, name='health_check'),
    path('ready/', views.readiness_check, name='readiness_check'),
    # Test endpoints
    path('test-azure-storage/', views.test_azure_storage, name='test_azure_storage'),
]