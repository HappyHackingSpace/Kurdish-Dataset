import os
import json
import tempfile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from scripts.corpus_processor import CorpusProcessor
from .forms import SubmissionForm
from .models import Submission
from datasets import load_dataset, Dataset
from huggingface_hub import login
from huggingface_hub import hf_hub_download, HfApi, CommitOperationAdd
from dotenv import load_dotenv
from scripts.corpus_processor import CorpusProcessor

# Load environment variables
load_dotenv()


def submit_pdf(request):
    """
    Handle PDF submission form, process the uploaded file and extract text.
    Redirects to preview page after successful submission.
    """
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save()
            file_path = os.path.join(settings.MEDIA_ROOT, submission.pdf_file.name)
            processor = CorpusProcessor(file_path)
            submission.extracted_text = processor.extract_text_only()
            submission.save()
            return redirect('submissions:preview_text', pk=submission.pk)
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
        submission.edited_text = request.POST.get('edited_text')
        submission.save()
        return redirect('submissions:thanks')
    return render(request, 'submissions/preview_text.html', {'submission': submission})


def thanks(request):
    """Display thank you page after successful submission."""
    return render(request, 'submissions/thanks.html')


@login_required
def admin_request_list(request):
    """Display list of pending submissions for admin review."""
    pending = Submission.objects.filter(status=Submission.STATUS_PENDING).order_by('-created_at')
    return render(request, 'submissions/admin_request_list.html', {'pending': pending})


@login_required
def admin_request_detail(request, pk):
    """
    Handle admin review of individual submissions.
    Supports accepting or rejecting submissions and updating the corpus.
    """
    submission = get_object_or_404(Submission, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        # Save edited text regardless of action
        new_text = request.POST.get('edited_text', '').strip()
        submission.edited_text = new_text
        submission.save()

        if action == 'accept':
            # Authenticate with Hugging Face
            login(token=os.getenv("HUGGINGFACE_TOKEN"))
            
            # Load existing dataset and combine with new text
            existing = load_dataset("happyhackingspace/kurdish-kurmanji-corpus", split="train")
            combined = Dataset.from_dict({"text": existing["text"] + [new_text]})
            combined.push_to_hub("happyhackingspace/kurdish-kurmanji-corpus", private=True)

            # Update JSON metadata file
            try:
                json_path = hf_hub_download(
                    repo_id="happyhackingspace/kurdish-kurmanji-corpus",
                    filename="kurmanji.json",
                    repo_type="dataset"
                )
                with open(json_path, encoding="utf-8") as f:
                    records = [json.loads(line) for line in f if line.strip()]
            except Exception:
                records = []

            # Add new record to metadata
            records.append({
                "file_name": os.path.basename(submission.pdf_file.name),
                "char_count": len(new_text),
                "word_count": len(new_text.split()),
                "text": new_text
            })

            # Create temporary file and push updates
            fd, tmp_path = tempfile.mkstemp(suffix=".jsonl")
            with os.fdopen(fd, 'w', encoding="utf-8") as tmp_file:
                for rec in records:
                    tmp_file.write(json.dumps(rec, ensure_ascii=False) + "\n")

            # Push changes to Hugging Face Hub
            api = HfApi()
            api.create_commit(
                repo_id="happyhackingspace/kurdish-kurmanji-corpus",
                repo_type="dataset",
                commit_message="Update kurmanji.json with admin-edited text",
                operations=[
                    CommitOperationAdd(
                        path_in_repo="kurmanji.json",
                        path_or_fileobj=tmp_path
                    )
                ]
            )
            os.remove(tmp_path)

            submission.delete()
            messages.success(request, 'Request accepted; edited text has been pushed.')
            return redirect('submissions:admin_request_list')

        elif action == 'reject':
            # Handle rejection by deleting the submission
            submission.delete()
            messages.info(request, 'Request rejected.')
            return redirect('submissions:admin_request_list')

    return render(request, 'submissions/admin_request_detail.html', {
        'submission': submission
    })

