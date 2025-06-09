from django.urls import path
from upload.views import upload_file, index as upload_page, translate_documents, download_file, list_user_files

urlpatterns = [
    path('', upload_page, name='upload_page'),
    path('upload/', upload_file, name='upload_file'),
    path('translate/', translate_documents, name='translate_documents'),
    path('download/<str:filename>/', download_file, name='download_file'),
    path('api/files/', list_user_files, name='list_user_files'),
]