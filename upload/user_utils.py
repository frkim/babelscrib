"""
User utilities for document access control and session management.
"""

import hashlib
import secrets
from django.utils import timezone
from datetime import timedelta
from .models import UserSession, Document
import logging

logger = logging.getLogger(__name__)

class UserIsolationService:
    """Service to handle user isolation and access control"""
    
    @staticmethod
    def generate_user_id_hash(email: str) -> str:
        """Generate a consistent hash for user identification"""
        return hashlib.sha256(email.lower().strip().encode()).hexdigest()[:16]
    
    @staticmethod
    def create_user_blob_name(email: str, original_filename: str) -> str:
        """Create a user-specific blob name to prevent conflicts"""
        user_hash = UserIsolationService.generate_user_id_hash(email)
        # Clean filename to prevent path traversal
        clean_filename = original_filename.replace('/', '_').replace('\\', '_')
        return f"{user_hash}/{clean_filename}"
    
    @staticmethod
    def get_or_create_session(request, email: str) -> str:
        """Get or create a session for the user"""
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        user_id_hash = UserIsolationService.generate_user_id_hash(email)
        
        # Clean up old sessions (older than 24 hours)
        cutoff_time = timezone.now() - timedelta(hours=24)
        UserSession.objects.filter(last_activity__lt=cutoff_time).delete()
        
        # Get or create session
        session, created = UserSession.objects.get_or_create(
            session_key=session_key,
            defaults={
                'user_email': email,
                'user_id_hash': user_id_hash
            }
        )
        
        if not created:
            # Update existing session
            session.user_email = email
            session.user_id_hash = user_id_hash
            session.last_activity = timezone.now()
            session.save()
        
        return session_key
    
    @staticmethod
    def get_user_from_session(request) -> tuple:
        """Get user email and hash from session"""
        session_key = request.session.session_key
        if not session_key:
            return None, None
        
        try:
            session = UserSession.objects.get(session_key=session_key)
            # Update last activity
            session.last_activity = timezone.now()
            session.save()
            return session.user_email, session.user_id_hash
        except UserSession.DoesNotExist:
            return None, None
    
    @staticmethod
    def validate_file_access(request, filename: str) -> bool:
        """Validate if the current user can access the specified file"""
        user_email, user_id_hash = UserIsolationService.get_user_from_session(request)
        if not user_email:
            return False
        
        # Check if the file belongs to the user
        try:
            # Try to find the document by user-specific blob name
            user_blob_name = UserIsolationService.create_user_blob_name(user_email, filename)
            
            # Check if the document exists and belongs to the user
            document = Document.objects.filter(
                user_email=user_email,
                user_blob_name__endswith=filename
            ).first()
            
            return document is not None
        except Exception as e:
            logger.error(f"Error validating file access for {user_email}, file {filename}: {str(e)}")
            return False
    
    @staticmethod
    def get_user_documents(request) -> list:
        """Get all documents belonging to the current user"""
        user_email, user_id_hash = UserIsolationService.get_user_from_session(request)
        if not user_email:
            return []
        
        return Document.objects.filter(user_email=user_email).order_by('-uploaded_at')
    
    @staticmethod
    def cleanup_user_files(email: str, blob_service_client, container_name: str):
        """Clean up files for a specific user"""
        user_id_hash = UserIsolationService.generate_user_id_hash(email)
        container_client = blob_service_client.get_container_client(container_name)
        
        try:
            # List blobs with the user's prefix
            blob_list = container_client.list_blobs(name_starts_with=f"{user_id_hash}/")
            deleted_count = 0
            
            for blob in blob_list:
                try:
                    container_client.delete_blob(blob.name)
                    deleted_count += 1
                    logger.info(f"Deleted blob: {blob.name}")
                except Exception as e:
                    logger.error(f"Failed to delete blob {blob.name}: {str(e)}")
            
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up files for user {email}: {str(e)}")
            return 0

def require_user_session(view_func):
    """Decorator to require a valid user session"""
    def wrapper(request, *args, **kwargs):
        user_email, user_id_hash = UserIsolationService.get_user_from_session(request)
        if not user_email:
            from django.http import JsonResponse
            return JsonResponse({'error': 'User session required'}, status=401)
        
        # Add user info to request for use in view
        request.user_email = user_email
        request.user_id_hash = user_id_hash
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
