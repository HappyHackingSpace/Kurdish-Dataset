import os
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
from .forms import SubmissionForm
from .models import SupabaseSubmission
from .pdf_processor import extract_text_from_pdf
import json
from huggingface_hub import HfApi
import requests
from pathlib import Path
from huggingface_hub import hf_hub_download
import tempfile

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

                # Read PDF content into memory
                pdf_content = pdf_file.read()

                # Upload PDF to Supabase Storage first
                supabase = SupabaseSubmission()
                bucket_path = f"pdfs/{pdf_file.name}"
                
                # Upload to Supabase Storage using the content
                storage_response = supabase.supabase.storage.from_("data_files").upload(
                    path=bucket_path,
                    file=pdf_content,
                    file_options={"cache-control": "3600", "upsert": "true"}
                )

                # Get public URL for the uploaded file
                pdf_url = supabase.supabase.storage.from_("data_files").get_public_url(bucket_path)
                
                # Extract text from PDF content
                try:
                    extracted_text = extract_text_from_pdf(pdf_content)
                    if not extracted_text:
                        logger.warning(f"No text extracted from PDF: {pdf_file.name}")
                        extracted_text = "No text could be extracted from the PDF."
                except Exception as e:
                    logger.error(f"Error extracting text from PDF: {str(e)}")
                    extracted_text = f"Error extracting text: {str(e)}"

                # Create submission in Supabase
                supabase_data = {
                    "name": data['name'],
                    "email": data['email'],
                    "subject": data['subject'],
                    "publication_date": data['publication_date'],
                    "author_source": data['author_source'],
                    "text_type": data['text_type'],
                    "pdf_file_url": pdf_url,
                    "extracted_text": extracted_text,
                    "edited_text": extracted_text,
                    "status": "pending"
                }

                supabase_result = supabase.create(supabase_data)
                
                if not supabase_result:
                    raise Exception("Failed to create submission in Supabase")

                messages.success(request, 'Submission uploaded successfully!')
                return redirect('submissions:preview_text', pk=supabase_result['id'])
                
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
    supabase = SupabaseSubmission()
    submission = supabase.get(pk)
    
    if not submission:
        messages.error(request, 'Submission not found')
        return redirect('submissions:submit_pdf')
    
    if request.method == 'POST':
        edited_text = request.POST.get('edited_text', '').strip()
        
        # Update Supabase
        supabase_data = {
            "edited_text": edited_text
        }
        supabase_result = supabase.update(pk, supabase_data)
        
        if not supabase_result:
            messages.error(request, 'Failed to update submission')
            return render(request, 'submissions/preview_text.html', {'submission': submission})

        return redirect('submissions:thanks')
        
    return render(request, 'submissions/preview_text.html', {'submission': submission})

def thanks(request):
    """Display thank you page after successful submission."""
    return render(request, 'submissions/thanks.html')

@login_required
def admin_request_list(request):
    """Display list of all submissions for admin review."""
    supabase = SupabaseSubmission()
    status = request.GET.get('status', 'pending')
    
    submissions = {
        'pending': supabase.list(status='pending'),
        'accepted': supabase.list(status='accepted'),
        'rejected': supabase.list(status='rejected')
    }
    
    return render(request, 'submissions/admin_request_list.html', {
        'submissions': submissions,
        'status': status
    })

@login_required
def admin_request_detail(request, pk):
    """Handle admin review of individual submissions."""
    supabase = SupabaseSubmission()
    submission = supabase.get(pk)

    if not submission:
        messages.error(request, 'Submission not found')
        return redirect('submissions:admin_request_list')

    if request.method == 'POST':
        action = request.POST.get('action')
        edited_text = request.POST.get('edited_text', '').strip()
        
        # Update Supabase
        supabase_data = {
            "edited_text": edited_text,
            "status": action
        }
        supabase_result = supabase.update(pk, supabase_data)
        
        if not supabase_result:
            messages.error(request, 'Failed to update submission')
            return render(request, 'submissions/admin_request_detail.html', {'submission': submission})

        if action == 'accept':
            # Push to Hugging Face
            if push_to_huggingface(submission):
                messages.success(request, 'Request accepted and pushed to Hugging Face!')
            else:
                messages.warning(request, 'Request accepted but failed to push to Hugging Face.')
        elif action == 'reject':
            messages.info(request, 'Request rejected.')

        return redirect('submissions:admin_request_list')

    return render(request, 'submissions/admin_request_detail.html', {'submission': submission})

def push_to_huggingface(submission):
    """
    Push accepted submission to Hugging Face repository using in-memory data
    """
    try:
        # Initialize Hugging Face API
        api = HfApi(token=settings.HUGGINGFACE_TOKEN)
        repo_id = "happyhackingspace/kurdish-kurmanji-corpus"

        # Calculate character and word count
        text = submission['edited_text'].strip()
        char_count = len(text)
        word_count = len(text.split())

        # Format only the new text: remove unnecessary line breaks and add newlines only after sentences
        new_text = ' '.join(text.split())
        formatted_new_text = new_text.replace('. ', '.\n').replace('! ', '!\n').replace('? ', '?\n')
        formatted_new_text = formatted_new_text.rstrip('\n')

        # Prepare JSON data
        json_data = {
            "document_subject": submission['subject'],
            "text_type": submission['text_type'],
            "author_source": submission['author_source'],
            "publication_date": submission['publication_date'],
            "created_at": submission['created_at'],
            "char_count": char_count,
            "word_count": word_count,
            "text": text
        }

        # Handle JSON file
        try:
            # Download existing JSON content
            existing_json_content = api.hf_hub_download(
                repo_id=repo_id,
                filename="kurmanji.json",
                repo_type="dataset",
                token=settings.HUGGINGFACE_TOKEN
            )
            
            # Read existing content
            with open(existing_json_content, "r", encoding="utf-8") as f:
                existing_lines = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.warning(f"Could not read existing JSON file: {str(e)}")
            existing_lines = []

        # Add new JSON data
        existing_lines.append(json.dumps(json_data, ensure_ascii=False))
        
        # Create in-memory JSON content
        json_content = "\n".join(existing_lines).encode('utf-8')

        # Upload JSON content
        api.upload_file(
            path_or_fileobj=json_content,
            path_in_repo="kurmanji.json",
            repo_id=repo_id,
            repo_type="dataset"
        )

        # Handle TXT file
        try:
            # Download existing TXT content
            existing_txt_content = api.hf_hub_download(
                repo_id=repo_id,
                filename="kurmanji.txt",
                repo_type="dataset",
                token=settings.HUGGINGFACE_TOKEN
            )
            
            # Read existing content
            with open(existing_txt_content, "r", encoding="utf-8") as f:
                existing_text = f.read().strip()
        except Exception as e:
            logger.warning(f"Could not read existing TXT file: {str(e)}")
            existing_text = ""

        # Combine existing and new text
        if existing_text:
            new_text = existing_text + "\n" + formatted_new_text
        else:
            new_text = formatted_new_text

        # Upload TXT content
        api.upload_file(
            path_or_fileobj=new_text.encode('utf-8'),
            path_in_repo="kurmanji.txt",
            repo_id=repo_id,
            repo_type="dataset"
        )

        logger.info(f"Successfully pushed submission {submission['id']} to Hugging Face")
        return True
    except Exception as e:
        logger.error(f"Error pushing to Hugging Face: {str(e)}")
        return False

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
                    submission = SupabaseSubmission()
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
    submissions = SupabaseSubmission().list(status='pending').order_by('-created_at')
    return render(request, 'submissions/admin.html', {'submissions': submissions})

@login_required
def edit_submission(request, pk):
    supabase = SupabaseSubmission()
    submission = supabase.get(pk)
    
    if not submission:
        messages.error(request, 'Submission not found')
        return redirect('submissions:admin_submissions')
    
    if request.method == 'POST':
        edited_text = request.POST.get('edited_text')
        if edited_text:
            supabase_data = {
                "edited_text": edited_text
            }
            supabase_result = supabase.update(pk, supabase_data)
            
            if not supabase_result:
                messages.error(request, 'Failed to update submission')
                return render(request, 'submissions/edit.html', {'submission': submission})
            
            messages.success(request, 'Submission updated successfully!')
            return redirect('submissions:admin_submissions')
    
    return render(request, 'submissions/edit.html', {'submission': submission})

@login_required
def delete_submission(request, pk):
    supabase = SupabaseSubmission()
    submission = supabase.get(pk)
    
    if not submission:
        messages.error(request, 'Submission not found')
        return redirect('submissions:admin_submissions')
    
    # Delete PDF file
    if submission['pdf_file_url']:
        try:
            # Extract file name from URL
            file_name = submission['pdf_file_url'].split('/')[-1]
            # Delete from Supabase Storage
            supabase.supabase.storage.from_("data_files").remove(f"pdfs/{file_name}")
        except Exception as e:
            logger.error(f"Error deleting file from Supabase Storage: {str(e)}")
    
    supabase.delete(pk)
    messages.success(request, 'Submission deleted successfully!')
    return redirect('submissions:admin_submissions')