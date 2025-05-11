from django import forms
from .models import Submission


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['name', 'email', 'subject', 'pdf_file']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Your email address'}),
            'subject': forms.TextInput(attrs={'placeholder': 'Document subject'}),
        }