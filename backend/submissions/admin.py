from django.contrib import admin
from .models import Submission

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'email', 'publication_date', 'status', 'created_at')
    list_filter = ('status', 'text_type', 'created_at')
    search_fields = ('subject', 'name', 'email', 'extracted_text', 'edited_text')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'subject', 'publication_date', 'author_source', 'text_type')
        }),
        ('Document', {
            'fields': ('pdf_file', 'extracted_text', 'edited_text')
        }),
        ('Status', {
            'fields': ('status', 'created_at')
        }),
    )
