import os
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
from .forms import SubmissionForm
from .models import Submission
from .pdf_processor import extract_text_from_pdf
import json
from huggingface_hub import HfApi
import requests
from pathlib import Path
from huggingface_hub import hf_hub_download

logger = logging.getLogger(__name__)

def submit_pdf(request):
    """
    Handle PDF submission form, process the uploaded file and extract text.
    Redirects to preview page after successful submission.
    """
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Get form data
                data = form.cleaned_data
                
                # Handle PDF file
                pdf_file = request.FILES.get('pdf_file')
                if not pdf_file:
                    raise ValueError("No PDF file provided")
                
                # Save PDF file
                pdf_path = os.path.join(settings.MEDIA_ROOT, 'pdfs', pdf_file.name)
                os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
                
                with open(pdf_path, 'wb+') as destination:
                    for chunk in pdf_file.chunks():
                        destination.write(chunk)
                
                # Extract text from PDF
                try:
                    extracted_text = extract_text_from_pdf(pdf_path)
                    if not extracted_text:
                        logger.warning(f"No text extracted from PDF: {pdf_file.name}")
                        extracted_text = "No text could be extracted from the PDF."
                except Exception as e:
                    logger.error(f"Error extracting text from PDF: {str(e)}")
                    extracted_text = f"Error extracting text: {str(e)}"
                
                # Create submission
                submission = Submission.objects.create(
                    name=data['name'],
                    email=data['email'],
                    subject=data['subject'],
                    publication_date=data['publication_date'],
                    author_source=data['author_source'],
                    text_type=data['text_type'],
                    pdf_file=pdf_file,
                    extracted_text=extracted_text,
                    edited_text=extracted_text  # Initially same as extracted text
                )
                
                messages.success(request, 'Submission uploaded successfully!')
                return redirect('submissions:preview_text', pk=submission.id)
                
            except Exception as e:
                logger.error(f"Error processing submission: {str(e)}")
                messages.error(request, f'Error processing submission: {str(e)}')
                return render(request, 'submissions/submit_pdf.html', {'form': form})
    else:
        form = SubmissionForm()
    
    return render(request, 'submissions/submit_pdf.html', {'form': form})

def preview_text(request, pk):
    """
    Display extracted text for preview and editing.
    Saves edited text and redirects to thank you page.
    """
    submission = get_object_or_404(Submission, pk=pk)
    
    if request.method == 'POST':
        edited_text = request.POST.get('edited_text', '').strip()
        submission.edited_text = edited_text
        submission.save()
        return redirect('submissions:thanks')
        
    return render(request, 'submissions/preview_text.html', {'submission': submission})

def thanks(request):
    """Display thank you page after successful submission."""
    return render(request, 'submissions/thanks.html')

@login_required
def admin_request_list(request):
    """Display list of all submissions for admin review."""
    submissions = {
        'pending': Submission.objects.filter(status='pending').order_by('-created_at'),
        'accepted': Submission.objects.filter(status='accepted').order_by('-created_at'),
        'rejected': Submission.objects.filter(status='rejected').order_by('-created_at')
    }
    return render(request, 'submissions/admin_request_list.html', {
        'pending': submissions['pending'],
        'submissions': submissions
    })

def push_to_huggingface(submission):
    """
    Push accepted submission to Hugging Face repository
    """
    try:
        # Initialize Hugging Face API
        api = HfApi(token=settings.HUGGINGFACE_TOKEN)
        repo_id = "happyhackingspace/kurdish-kurmanji-corpus"

        # Calculate character and word count
        text = submission.edited_text.strip()
        char_count = len(text)
        word_count = len(text.split())

        # Format text with newlines after each sentence
        formatted_text = text.replace('. ', '.\n').replace('! ', '!\n').replace('? ', '?\n')

        # Prepare JSON data with the required structure
        json_data = {
            "document_subject": submission.subject,
            "text_type": submission.get_text_type_display(),
            "author_source": submission.author_source,
            "publication_date": submission.publication_date,
            "created_at": submission.created_at.strftime("%Y-%m-%d"),
            "char_count": char_count,
            "word_count": word_count,
            "text": text
        }

        # Handle JSON file
        try:
            # Try to download existing JSON file
            existing_json_path = hf_hub_download(
                repo_id=repo_id,
                filename="kurmanji.json",
                repo_type="dataset",
                token=settings.HUGGINGFACE_TOKEN
            )
            with open(existing_json_path, "r", encoding="utf-8") as f:
                existing_lines = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.warning(f"Could not read existing JSON file: {str(e)}")
            existing_lines = []

        # Add new JSON data
        existing_lines.append(json.dumps(json_data, ensure_ascii=False))
        
        # Create temporary file for combined JSON
        temp_json = Path("temp_kurmanji.json")
        with temp_json.open("w", encoding="utf-8") as f:
            for line in existing_lines:
                f.write(line + "\n")

        # Upload combined JSON file
        api.upload_file(
            path_or_fileobj=temp_json,
            path_in_repo="kurmanji.json",
            repo_id=repo_id,
            repo_type="dataset"
        )

        # Handle TXT file
        try:
            # Try to download existing TXT file
            existing_txt_path = hf_hub_download(
                repo_id=repo_id,
                filename="kurmanji.txt",
                repo_type="dataset",
                token=settings.HUGGINGFACE_TOKEN
            )
            with open(existing_txt_path, "r", encoding="utf-8") as f:
                existing_text = f.read().strip()
        except Exception as e:
            logger.warning(f"Could not read existing TXT file: {str(e)}")
            existing_text = ""

        # Combine existing and new text
        if existing_text:
            new_text = existing_text + "\n\n" + formatted_text
        else:
            new_text = formatted_text

        # Create temporary file for combined TXT
        temp_txt = Path("temp_kurmanji.txt")
        with temp_txt.open("w", encoding="utf-8") as f:
            f.write(new_text)

        # Upload combined TXT file
        api.upload_file(
            path_or_fileobj=temp_txt,
            path_in_repo="kurmanji.txt",
            repo_id=repo_id,
            repo_type="dataset"
        )

        # Clean up temporary files
        if temp_json.exists():
            os.remove(temp_json)
        if temp_txt.exists():
            os.remove(temp_txt)

        logger.info(f"Successfully pushed submission {submission.id} to Hugging Face")
        return True
    except Exception as e:
        logger.error(f"Error pushing to Hugging Face: {str(e)}")
        return False

@login_required
def admin_request_detail(request, pk):
    """Handle admin review of individual submissions."""
    submission = get_object_or_404(Submission, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        edited_text = request.POST.get('edited_text', '').strip()
        
        # Update edited text
        submission.edited_text = edited_text
        
        if action == 'accept':
            submission.status = 'accepted'
            # Push to Hugging Face
            if push_to_huggingface(submission):
                messages.success(request, 'Request accepted and pushed to Hugging Face!')
            else:
                messages.warning(request, 'Request accepted but failed to push to Hugging Face.')
        elif action == 'reject':
            submission.status = 'rejected'
            messages.info(request, 'Request rejected.')
        
        submission.save()
        return redirect('submissions:admin_request_list')
    
    return render(request, 'submissions/admin_request_detail.html', {'submission': submission})

def upload_submission(request):
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Get form data
                data = form.cleaned_data
                
                # Handle PDF file
                pdf_file = request.FILES.get('pdf_file')
                if not pdf_file:
                    raise ValueError("No PDF file provided")
                
                # Save PDF file
                pdf_path = os.path.join(settings.MEDIA_ROOT, 'pdfs', pdf_file.name)
                os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
                
                with open(pdf_path, 'wb+') as destination:
                    for chunk in pdf_file.chunks():
                        destination.write(chunk)
                
                # Extract text from PDF
                try:
                    extracted_text = extract_text_from_pdf(pdf_path)
                    if not extracted_text:
                        logger.warning(f"No text extracted from PDF: {pdf_file.name}")
                        extracted_text = "No text could be extracted from the PDF."
                except Exception as e:
                    logger.error(f"Error extracting text from PDF: {str(e)}")
                    extracted_text = f"Error extracting text: {str(e)}"
                
                # Create submission data
                submission_data = {
                    'name': data['name'],
                    'email': data['email'],
                    'subject': data['subject'],
                    'publication_date': data['publication_date'],
                    'author_source': data['author_source'],
                    'text_type': data['text_type'],
                    'pdf_file_url': f"/media/pdfs/{pdf_file.name}",
                    'extracted_text': extracted_text,
                    'edited_text': extracted_text  # Initially same as extracted text
                }
                
                # Save to Supabase
                try:
                    submission = Submission.objects.create(
                        name=data['name'],
                        email=data['email'],
                        subject=data['subject'],
                        publication_date=data['publication_date'],
                        author_source=data['author_source'],
                        text_type=data['text_type'],
                        pdf_file=pdf_file,
                        extracted_text=extracted_text,
                        edited_text=extracted_text  # Initially same as extracted text
                    )
                    messages.success(request, 'Submission uploaded successfully!')
                    return redirect('submission_success')
                except Exception as e:
                    logger.error(f"Error saving to Supabase: {str(e)}")
                    messages.error(request, f'Error saving submission: {str(e)}')
                    return render(request, 'submissions/upload.html', {'form': form})
                
            except Exception as e:
                logger.error(f"Error processing submission: {str(e)}")
                messages.error(request, f'Error processing submission: {str(e)}')
                return render(request, 'submissions/upload.html', {'form': form})
    else:
        form = SubmissionForm()
    
    return render(request, 'submissions/upload.html', {'form': form})

def submission_success(request):
    return render(request, 'submissions/success.html')

@login_required
def admin_submissions(request):
    submissions = Submission.objects.filter(status='pending').order_by('-created_at')
    return render(request, 'submissions/admin.html', {'submissions': submissions})

@login_required
def edit_submission(request, pk):
    submission = get_object_or_404(Submission, pk=pk)
    
    if request.method == 'POST':
        edited_text = request.POST.get('edited_text')
        if edited_text:
            submission.edited_text = edited_text
            submission.save()
            messages.success(request, 'Submission updated successfully!')
        return redirect('submissions:admin_submissions')
    
    return render(request, 'submissions/edit.html', {'submission': submission})

@login_required
def delete_submission(request, pk):
    submission = get_object_or_404(Submission, pk=pk)
    
    # Delete PDF file
    if submission.pdf_file:
        try:
            os.remove(submission.pdf_file.path)
        except:
            pass  # Ignore file deletion errors
    
    submission.delete()
    messages.success(request, 'Submission deleted successfully!')
    return redirect('submissions:admin_submissions')