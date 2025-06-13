import os
import json
from datetime import datetime
from huggingface_hub import HfApi, create_repo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_new_dataset():
    # Define temporary directory name at the beginning
    temp_dir = "temp_dataset_files"
    
    try:
        # Get Hugging Face API token
        hf_token = os.getenv("HUGGINGFACE_TOKEN")
        if not hf_token:
            raise ValueError("HUGGINGFACE_TOKEN environment variable is not set")

        # Dataset bilgileri
        dataset_name = "kurdish-kurmanji-corpus"
        repo_id = f"happyhackingspace/{dataset_name}"
        # Create Hugging Face API client
        api = HfApi()
        
        try:
            # Create new dataset repository
            create_repo(
                repo_id=repo_id,
                repo_type="dataset",
                private=True,
                token=hf_token
            )
            print(f"Yeni dataset repository'si oluşturuldu: {repo_id}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"Dataset zaten mevcut: {repo_id}")
            else:
                raise e
        
        # Create temporary directory
        os.makedirs(temp_dir, exist_ok=True)
        
        # Create sample data
        sample_data = {
            "document_subject": "",
            "text_type": "",
            "author_source": "",
            "publication_date": datetime.now().strftime("%Y-%m-%d"),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "char_count": 0,
            "word_count": 0,
            "text": ""
        }
        
        # Create JSON file
        json_path = os.path.join(temp_dir, "kurmanji.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump([sample_data], f, ensure_ascii=False, indent=2)
        
        # Create TXT file
        txt_path = os.path.join(temp_dir, "kurmanji.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(sample_data["text"])
        
        # Upload files to Hugging Face
        api.upload_file(
            path_or_fileobj=json_path,
            path_in_repo="kurmanji.json",
            repo_id=repo_id,
            repo_type="dataset",
            token=hf_token
        )
        
        api.upload_file(
            path_or_fileobj=txt_path,
            path_in_repo="kurmanji.txt",
            repo_id=repo_id,
            repo_type="dataset",
            token=hf_token
        )
        
        print(f"Dataset dosyaları başarıyla yüklendi: {repo_id}")
        
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
    
    finally:
        # Clean up temporary files
        if os.path.exists(temp_dir):
            for file in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file))
            os.rmdir(temp_dir)

if __name__ == "__main__":
    create_new_dataset() 