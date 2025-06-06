from django.contrib import admin
from .models import Document  # Assuming you have a Document model in models.py

admin.site.register(Document)  # Register the Document model with the admin site