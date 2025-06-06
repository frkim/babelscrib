from django.urls import path
from upload.views import upload_file, index as upload_page

urlpatterns = [
    path('', upload_page, name='upload_page'),
    path('upload/', upload_file, name='upload_file'),
]