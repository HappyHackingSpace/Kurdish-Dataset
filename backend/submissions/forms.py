from django import forms
from .models import Submission


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['name', 'email', 'subject', 'publication_date', 'author_source', 'text_type', 'pdf_file']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Your email address'}),
            'subject': forms.TextInput(attrs={'placeholder': 'Document subject'}),
            'publication_date': forms.TextInput(
                attrs={
                    'placeholder': 'dd-mm-yyyy',
                    'pattern': r'\d{2}-\d{2}-\d{4}',
                    'maxlength': '10',
                    'oninput': 'formatDate(this)',
                    'onkeydown': 'handleBackspace(this, event)'
                }
            ),
            'author_source': forms.TextInput(attrs={'placeholder': 'Author or source information'}),
            'text_type': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_publication_date(self):
        publication_date = self.cleaned_data.get('publication_date')
        if not publication_date:
            return ''
        return publication_date

    class Media:
        js = ('js/date_formatter.js',)