from django.db import models
from django.conf import settings
from supabase import create_client
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

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
    TABLE = 'submission_logs'

    def __init__(self):
        self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.table = self.supabase.table(self.TABLE)

    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            payload = {"action": "create", **data}
            res = self.table.insert(payload).execute()
            return (res.data or [None])[0]
        except Exception as e:
            logger.exception("create failed: %s", e)
            return None

    def get(self, submission_id: str) -> Optional[Dict[str, Any]]:
        try:
            res = self.table.select("*").eq('id', submission_id).single().execute()
            return res.data
        except Exception as e:
            logger.exception("get failed: %s", e)
            return None

    def update(self, submission_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            payload = {"action": data.get("action", "update"), **{k:v for k,v in data.items() if k != "action"}}
            res = self.table.update(payload).eq('id', submission_id).execute()
            return (res.data or [None])[0]
        except Exception as e:
            logger.exception("update failed: %s", e)
            return None

    def delete(self, submission_id: str) -> bool:
        try:
            self.table.delete().eq('id', submission_id).execute()
            return True
        except Exception as e:
            logger.exception("delete failed: %s", e)
            return False

    def list(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            q = self.table.select("*")
            if status:
                q = q.eq('status', status)
            return q.order('created_at', desc=True).execute().data or []
        except Exception as e:
            logger.exception("list failed: %s", e)
            return []
