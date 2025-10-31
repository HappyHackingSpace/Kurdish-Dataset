# Kurdish Data Collector

Kurdish Data Collector is a Django-based platform for collecting and processing Kurdish (Kurmanji) texts from uploaded PDF documents. Submitted texts are extracted, reviewed, and stored in a managed database, then published to a Hugging Face dataset to support open Kurdish language resources.

---

## Features
- PDF upload and automatic text extraction (PyPDF2 + PDFMiner)
- Supabase Storage integration for file handling
- Admin panel for reviewing, accepting, or rejecting submissions
- Automatic Hugging Face dataset updates for accepted submissions
- Secure admin authentication

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/HappyHackingSpace/Kurdish-Dataset.git
cd Kurdish-Dataset/backend
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Copy `.env.example` and rename it to `.env`, then fill in your credentials:
```bash
cp ../.env.example ../.env
```

### 5. Run database migrations
```bash
python manage.py migrate
```

### 6. Create a superuser (for admin access)
```bash
python manage.py createsuperuser
```

### 7. Start the development server
```bash
python manage.py runserver localhost:8000
```

Access the app at **http://localhost:8000**

---

## Environment Variables
```text
DJANGO_DEBUG=1
SECRET_KEY=your-secret-key
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CSRF_TRUSTED=http://127.0.0.1:8000,http://localhost:8000

SUPABASE_URL=https://your-ref.supabase.co

SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_KEY=your-supabase-key
SUPABASE_BUCKET=your-bucket

HUGGINGFACE_TOKEN=your-huggingface-token
```

## License
Licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.