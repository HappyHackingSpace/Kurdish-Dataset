import os
from dotenv import load_dotenv
from supabase import create_client
import uuid
from datetime import datetime, timezone, timedelta

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# İstanbul için UTC+3
istanbul_tz = timezone(timedelta(hours=3))

def create_submission(data):
    """
    Create a new submission in Supabase
    """
    submission = {
        "id": str(uuid.uuid4()),
        "name": data.get('name'),
        "email": data.get('email'),
        "subject": data.get('subject'),
        "publication_date": data.get('publication_date', '01-01-1000'),
        "author_source": data.get('author_source', 'Unknown'),
        "text_type": data.get('text_type'),
        "pdf_file_url": data.get('pdf_file_url'),
        "extracted_text": data.get('extracted_text', ''),
        "edited_text": data.get('edited_text', ''),
        "status": "pending",
        "created_at": datetime.now(istanbul_tz).isoformat()
    }
    
    response = supabase_admin.table("submissions").insert(submission).execute()
    return response.data[0] if response.data else None

def get_submission(submission_id):
    """
    Get a submission by ID
    """
    response = supabase_admin.table("submissions").select("*").eq("id", submission_id).single().execute()
    return response.data if response.data else None

def get_pending_submissions():
    """
    Get all pending submissions
    """
    response = supabase_admin.table("submissions").select("*").eq("status", "pending").order("created_at", desc=True).execute()
    return response.data if response.data else []

def update_submission(submission_id, data):
    """
    Update a submission
    """
    response = supabase_admin.table("submissions").update(data).eq("id", submission_id).execute()
    return response.data[0] if response.data else None

def delete_submission(submission_id):
    """
    Delete a submission
    """
    response = supabase_admin.table("submissions").delete().eq("id", submission_id).execute()
    return response.data[0] if response.data else None






import os
from supabase import create_client, Client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

#supabase.storage.create_bucket("data_files")
response = supabase.storage.empty_bucket("data_files")



local_file_path = r"D:\github-cli\hhs\Kurdish-Dataset\pdfs\ciroka_rovi_u_ser.pdf"
bucket_path = "pdfs/ciroka_rovi_u_ser.pdf"

with open(local_file_path, "rb") as f:
    response = (
        supabase.storage
        .from_("data_files")
        .upload(
            path=bucket_path,
            file=f,
            file_options={"cache-control": "3600", "upsert": False}
        )
    )

data = {
    "name": "John Doe",
    "email": "john@example.com",
    "subject": "Article on AI",
    "publication_date": "2024-05-01",
    "author_source": "John D.",
    "text_type": "Research",
    "pdf_file_url": "https://example.com/file.pdf",
    "extracted_text": "This is the extracted text.",
    "edited_text": "This is the edited text.",
    "status": "pending"
}

response = supabase.table("submission_logs").insert(data).execute()