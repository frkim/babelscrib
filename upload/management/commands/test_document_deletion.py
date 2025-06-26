from django.core.management.base import BaseCommand
from django.utils import timezone
from upload.models import Document, UserSession
from upload.views import delete_user_documents, create_user_hash
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test the document deletion functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='User email to test deletion for',
            default='test@example.com'
        )
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Create test documents before testing deletion',
        )

    def handle(self, *args, **options):
        user_email = options['user_email']
        create_test_data = options['create_test_data']
        
        self.stdout.write(f"Testing document deletion for user: {user_email}")
        
        # Create user hash
        user_id_hash = create_user_hash(user_email)
        self.stdout.write(f"User ID hash: {user_id_hash}")
        
        if create_test_data:
            # Create some test documents
            self.stdout.write("Creating test documents...")
            
            test_docs = [
                {'title': 'Test Document 1.pdf', 'blob_name': 'test1.pdf'},
                {'title': 'Test Document 2.docx', 'blob_name': 'test2.docx'},
                {'title': 'Test Document 3.txt', 'blob_name': 'test3.txt'},
            ]
            
            for doc_data in test_docs:
                document = Document(
                    title=doc_data['title'],
                    user_email=user_email,
                    user_id_hash=user_id_hash,
                    blob_name=doc_data['blob_name'],
                    user_blob_name=f"{user_id_hash}/{doc_data['blob_name']}",
                    is_translated=False
                )
                document.save()
                self.stdout.write(f"  Created: {doc_data['title']}")
        
        # Check existing documents before deletion
        existing_docs = Document.objects.filter(user_id_hash=user_id_hash)
        self.stdout.write(f"Found {existing_docs.count()} existing documents before deletion:")
        for doc in existing_docs:
            self.stdout.write(f"  - {doc.title} (blob: {doc.user_blob_name})")
        
        if existing_docs.count() == 0:
            self.stdout.write(self.style.WARNING("No documents found to delete. Use --create-test-data to create test documents first."))
            return
        
        # Test the deletion function
        self.stdout.write("\nTesting document deletion...")
        
        try:
            result = delete_user_documents(user_id_hash, user_email)
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS(f"✓ Deletion successful: {result['message']}"))
                self.stdout.write(f"  Database records deleted: {result['deleted_count']}")
                self.stdout.write(f"  Source blobs deleted: {result['blob_deletions']['source']}")
                self.stdout.write(f"  Target blobs deleted: {result['blob_deletions']['target']}")
            else:
                self.stdout.write(self.style.ERROR(f"✗ Deletion failed: {result['message']}"))
                self.stdout.write(f"  Database records deleted: {result['deleted_count']}")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Exception during deletion: {str(e)}"))
        
        # Check documents after deletion
        remaining_docs = Document.objects.filter(user_id_hash=user_id_hash)
        self.stdout.write(f"\nDocuments remaining after deletion: {remaining_docs.count()}")
        
        if remaining_docs.count() == 0:
            self.stdout.write(self.style.SUCCESS("✓ All documents successfully deleted from database"))
        else:
            self.stdout.write(self.style.WARNING("⚠ Some documents still remain:"))
            for doc in remaining_docs:
                self.stdout.write(f"  - {doc.title}")
        
        self.stdout.write("\nTest completed.")
