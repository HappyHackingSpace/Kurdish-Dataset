import os
import logging
import tempfile
from io import BytesIO

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages

from .forms import SubmissionForm
from .models import SupabaseSubmission
from .pdf_processor import extract_text_from_pdf

from huggingface_hub import HfApi, hf_hub_download
import json

logger = logging.getLogger(__name__)
BUCKET = getattr(settings, "SUPABASE_BUCKET", "pdfs")


def _signed_url_for_key(supabase_client, key: str, expires: int = 3600) -> str | None:
    try:
        if not key:
            return None
        resp = supabase_client.storage.from_(BUCKET).create_signed_url(key, expires)
        return resp.get("signedURL") or resp.get("signed_url")
    except Exception as e:
        logger.warning("Could not generate signed URL: %s", e)
        return None


def submit_pdf(request):
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                data = form.cleaned_data

                pdf_file = request.FILES.get('pdf_file')
                if not pdf_file:
                    raise ValueError("No PDF file provided")

                pdf_bytes = pdf_file.read()

                sb = SupabaseSubmission().supabase
                object_name = f"{pdf_file.name}"
                storage = sb.storage.from_(BUCKET)
                storage.upload(
                    object_name,
                    pdf_bytes,
                    {"contentType": "application/pdf", "upsert": "true"},
                )

                pdf_key = object_name

                fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
                try:
                    with os.fdopen(fd, "wb") as tmpf:
                        tmpf.write(pdf_bytes)
                        tmpf.flush()
                    extracted_text = extract_text_from_pdf(tmp_path)
                finally:
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass

                if not extracted_text:
                    logger.warning("No text extracted from PDF: %s", pdf_file.name)
                    extracted_text = "No text could be extracted from the PDF."

                supabase_data = {
                    "name": data['name'],
                    "email": data['email'],
                    "subject": data['subject'],
                    "publication_date": data['publication_date'],
                    "author_source": data['author_source'],
                    "text_type": data['text_type'],
                    "pdf_file_url": pdf_key,
                    "extracted_text": extracted_text,
                    "edited_text": extracted_text,
                    "status": "pending",
                }

                created = SupabaseSubmission().create({"action": "create", **supabase_data})
                if not created:
                    raise Exception("Failed to create submission in Supabase")

                messages.success(request, 'Submission uploaded successfully!')
                return redirect('submissions:preview_text', pk=created['id'])

            except Exception as e:
                logger.error("Error processing submission: %s", e)
                messages.error(request, f'Error processing submission: {e}')
                return render(request, 'submissions/submit_pdf.html', {'form': form})
    else:
        form = SubmissionForm()

    return render(request, 'submissions/submit_pdf.html', {'form': form})


def preview_text(request, pk):
    supabase = SupabaseSubmission()
    submission = supabase.get(pk)

    if not submission:
        messages.error(request, 'Submission not found.')
        return redirect('submissions:submit_pdf')

    if request.method == 'POST':
        edited_text = request.POST.get('edited_text', '').strip()

        res = supabase.update(pk, {"edited_text": edited_text, "action": "update"})
        if not res:
            messages.error(request, 'Failed to update submission.')
            return render(request, 'submissions/preview_text.html', {'submission': submission})

        return redirect('submissions:thanks')

    preview_url = _signed_url_for_key(supabase.supabase, submission.get("pdf_file_url", "")) or ""
    return render(request, 'submissions/preview_text.html', {'submission': submission, 'preview_url': preview_url})


def thanks(request):
    return render(request, 'submissions/thanks.html')


@login_required
def admin_request_list(request):
    supabase = SupabaseSubmission()
    status = request.GET.get('status', 'pending')

    submissions = {
        'pending': supabase.list(status='pending'),
        'accepted': supabase.list(status='accepted'),
        'rejected': supabase.list(status='rejected'),
    }

    return render(request, 'submissions/admin_request_list.html', {
        'submissions': submissions,
        'status': status
    })


@login_required
def admin_request_detail(request, pk):
    supabase = SupabaseSubmission()
    submission = supabase.get(pk)
    if not submission:
        messages.error(request, 'Submission not found.')
        return redirect('submissions:admin_request_list')

    if request.method == 'POST':
        action = request.POST.get('action', '').strip().lower()
        edited_text = request.POST.get('edited_text', '').strip()

        status_map = {'accept': 'accepted', 'reject': 'rejected'}
        new_status = status_map.get(action, action)

        res = supabase.update(pk, {"edited_text": edited_text, "status": new_status, "action": "update"})
        if not res:
            messages.error(request, 'Failed to update submission.')
            return render(request, 'submissions/admin_request_detail.html', {'submission': submission})

        if new_status == 'accepted':
            payload = {**submission, "edited_text": edited_text}
            if push_to_huggingface(payload):
                messages.success(request, 'Request accepted and pushed to Hugging Face.')
            else:
                messages.warning(request, 'Request accepted but failed to push to Hugging Face.')
        elif new_status == 'rejected':
            messages.info(request, 'Request rejected.')

        return redirect('submissions:admin_request_list')

    preview_url = _signed_url_for_key(supabase.supabase, submission.get("pdf_file_url", "")) or ""
    return render(request, 'submissions/admin_request_detail.html', {'submission': submission, 'preview_url': preview_url})


def push_to_huggingface(submission) -> bool:
    try:
        api = HfApi(token=settings.HUGGINGFACE_TOKEN)
        repo_id = "happyhackingspace/kurdish-kurmanji-corpus"

        text = (submission.get('edited_text') or "").strip()
        char_count = len(text)
        word_count = len(text.split())

        new_text = ' '.join(text.split())
        formatted_new_text = new_text.replace('. ', '.\n').replace('! ', '!\n').replace('? ', '?\n').rstrip('\n')

        json_data = {
            "document_subject": submission.get('subject'),
            "text_type": submission.get('text_type'),
            "author_source": submission.get('author_source'),
            "publication_date": submission.get('publication_date'),
            "created_at": submission.get('created_at'),
            "char_count": char_count,
            "word_count": word_count,
            "text": text,
        }

        try:
            existing_json_path = hf_hub_download(
                repo_id=repo_id, filename="kurmanji.json", repo_type="dataset",
                token=settings.HUGGINGFACE_TOKEN
            )
            with open(existing_json_path, "r", encoding="utf-8") as f:
                existing_lines = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.warning("Could not read existing JSON file: %s", e)
            existing_lines = []

        existing_lines.append(json.dumps(json_data, ensure_ascii=False))
        api.upload_file(
            path_or_fileobj=BytesIO(("\n".join(existing_lines)).encode("utf-8")),
            path_in_repo="kurmanji.json", repo_id=repo_id, repo_type="dataset"
        )

        try:
            existing_txt_path = hf_hub_download(
                repo_id=repo_id, filename="kurmanji.txt", repo_type="dataset",
                token=settings.HUGGINGFACE_TOKEN
            )
            with open(existing_txt_path, "r", encoding="utf-8") as f:
                existing_text = f.read().strip()
        except Exception as e:
            logger.warning("Could not read existing TXT file: %s", e)
            existing_text = ""

        merged = (existing_text + "\n" + formatted_new_text).strip() if existing_text else formatted_new_text
        api.upload_file(
            path_or_fileobj=BytesIO(merged.encode("utf-8")),
            path_in_repo="kurmanji.txt", repo_id=repo_id, repo_type="dataset"
        )

        logger.info("Pushed submission %s to Hugging Face", submission.get('id'))
        return True
    except Exception as e:
        logger.error("Hugging Face push failed: %s", e)
        return False


@login_required
def admin_submissions(request):
    submissions = SupabaseSubmission().list(status='pending')
    return render(request, 'submissions/admin.html', {'submissions': submissions})


@login_required
def edit_submission(request, pk):
    supabase = SupabaseSubmission()
    submission = supabase.get(pk)

    if not submission:
        messages.error(request, 'Submission not found.')
        return redirect('submissions:admin_submissions')

    if request.method == 'POST':
        edited_text = request.POST.get('edited_text')
        if edited_text:
            res = supabase.update(pk, {"edited_text": edited_text, "action": "update"})
            if not res:
                messages.error(request, 'Failed to update submission.')
                return render(request, 'submissions/edit.html', {'submission': submission})

            messages.success(request, 'Submission updated successfully.')
            return redirect('submissions:admin_submissions')

    return render(request, 'submissions/edit.html', {'submission': submission})


@login_required
def delete_submission(request, pk):
    supabase = SupabaseSubmission()
    submission = supabase.get(pk)
    if not submission:
        messages.error(request, 'Submission not found.')
        return redirect('submissions:admin_submissions')

    key = submission.get('pdf_file_url')
    if key:
        try:
            supabase.supabase.storage.from_(BUCKET).remove([key])
        except Exception as e:
            logger.error("Error deleting file from Supabase Storage: %s", e)

    supabase.delete(pk)
    messages.success(request, 'Submission deleted successfully.')
    return redirect('submissions:admin_submissions')
