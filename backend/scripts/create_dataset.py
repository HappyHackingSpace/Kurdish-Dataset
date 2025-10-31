import os
import json
from datetime import datetime
from huggingface_hub import HfApi, create_repo
from dotenv import load_dotenv

load_dotenv()

def create_new_dataset():
    temp_dir = "temp_dataset_files"
    
    try:
        hf_token = os.getenv("HUGGINGFACE_TOKEN")
        if not hf_token:
            raise ValueError("HUGGINGFACE_TOKEN environment variable is not set")

        dataset_name = "kurdish-kurmanji-corpus"
        repo_id = f"happyhackingspace/{dataset_name}"
        api = HfApi()
        
        try:
            create_repo(
                repo_id=repo_id,
                repo_type="dataset",
                private=True,
                token=hf_token
            )
            print(f"New dataset repository created: {repo_id}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"Dataset already exists: {repo_id}")
            else:
                raise e
        
        os.makedirs(temp_dir, exist_ok=True)
        
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
        
        json_path = os.path.join(temp_dir, "kurmanji.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump([sample_data], f, ensure_ascii=False, indent=2)
        
        txt_path = os.path.join(temp_dir, "kurmanji.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(sample_data["text"])
        
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
        
        print(f"Dataset files loaded successfully: {repo_id}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    finally:
        if os.path.exists(temp_dir):
            for file in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file))
            os.rmdir(temp_dir)

if __name__ == "__main__":
    create_new_dataset() 