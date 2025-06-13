from django.db import models
from django.utils import timezone
from supabase import create_client
#from django.conf import settings
from dotenv import load_dotenv
import os

load_dotenv()

class Submission(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    TEXT_TYPE_CHOICES = [
        ('news', 'News'),
        ('literary_text', 'Literary Text'),
        ('legal_document', 'Legal Document'),
        ('technical_guide', 'Technical Guide'),
        ('academic_article', 'Academic Article'),
        ('official_document', 'Official Document'),
        ('educational_material', 'Educational Material'),
        ('report', 'Report'),
        ('guide_manual', 'Guide / Manual'),
        ('personal_writing', 'Personal Writing'),
        ('advertisement_promotion', 'Advertisement / Promotion'),
        ('review_criticism', 'Review / Criticism'),
        ('religious_text', 'Religious Text'),
        ('web_content', 'Web Content'),
        ('qa_forum', 'Q&A / Forum'),
        ('interview', 'Interview'),
        ('commercial_document', 'Commercial Document'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    publication_date = models.CharField(
        max_length=10,
        verbose_name='Publication Date',
        default='01-01-1000'
    )
    author_source = models.CharField(
        max_length=200,
        verbose_name='Author / Source Information',
        default='Unknown'
    )
    text_type = models.CharField(
        max_length=50,
        verbose_name='Text Type / Category',
        choices=TEXT_TYPE_CHOICES,
        default='other'
    )
    pdf_file = models.FileField(upload_to='pdfs/')
    extracted_text = models.TextField(blank=True)
    edited_text = models.TextField(blank=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"

    class Meta:
        ordering = ['-created_at']

class SupabaseSubmission:
    def __init__(self):
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
        self.table = self.supabase.table('submission_logs')

    def create(self, data):
        """
        Create a new submission in Supabase
        """
        try:
            response = self.table.insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating submission: {str(e)}")
            return None

    def get(self, submission_id):
        """
        Get a submission by ID
        """
        try:
            response = self.table.select("*").eq('id', submission_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting submission: {str(e)}")
            return None

    def update(self, submission_id, data):
        """
        Update a submission
        """
        try:
            response = self.table.update(data).eq('id', submission_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating submission: {str(e)}")
            return None

    def delete(self, submission_id):
        """
        Delete a submission
        """
        try:
            response = self.table.delete().eq('id', submission_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting submission: {str(e)}")
            return False

    def list(self, status=None):
        """
        List all submissions, optionally filtered by status
        """
        try:
            query = self.table.select("*")
            if status:
                query = query.eq('status', status)
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error listing submissions: {str(e)}")
            return []
