import re
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LAParams
from datasets import load_dataset, Dataset
from huggingface_hub import login, hf_hub_download, upload_file

load_dotenv()

class CorpusProcessor:
    def __init__(self, source_pdf_path, start_page=None, end_page=None):
        """
        Extracts and processes text from a PDF file.

        Args:
            source_pdf_path (str or Path): Path to the PDF file.
            start_page (int, optional): Start page (1-indexed). Defaults to None.
            end_page (int, optional): End page (inclusive, 1-indexed). Defaults to None.
        """
        self.source_pdf_path = Path(source_pdf_path)
        self.start_page = start_page
        self.end_page = end_page

        # Paths
        self.paths = {
            "raw_txt": Path("data/raw/raw_kurmanji.txt"),
            "processed_txt": Path("data/processed/kurmanji.txt"),
            "processed_jsonl": Path("data/processed/kurmanji.json"),
            "upload_txt": Path("data/processed/kurmanji.txt"),
            "upload_jsonl": "kurmanji.json"
        }

        self.repo_id = "happyhackingspace/kurdish-kurmanji-corpus"
        self.hf_token = os.getenv("HUGGINGFACE_TOKEN")
        login(token=self.hf_token)

        # Process immediately
        self.cleaned_text = self._extract_clean_text()
        self._save_raw_text(self.cleaned_text)

    def _extract_clean_text(self):
        """Extract and clean text from the PDF."""
        text = ""
        page_range = range(self.start_page - 1, self.end_page) if self.start_page and self.end_page else None

        for page_layout in extract_pages(self.source_pdf_path, page_numbers=page_range, laparams=LAParams()):
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text += element.get_text()

        # Clean the text
        cleaned = re.sub(r'[^\w\s\.,\']+', '', text).replace('\n', ' ').strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'(?<!\.)\.\s+', '.\n', cleaned)

        return cleaned

    def _save_raw_text(self, text, mode="w"):
        """Save cleaned text to raw file."""
        self.paths["raw_txt"].parent.mkdir(parents=True, exist_ok=True)
        with self.paths["raw_txt"].open(mode, encoding="utf-8") as f:
            f.write(text + "\n")

    def finalize_and_save_processed_data(self):
        """
        Append the raw text into processed TXT and JSONL files.
        Should be called after manual validation.
        """
        with self.paths["raw_txt"].open("r", encoding="utf-8") as f:
            content = f.read().strip()

        record = {
            "file_name": self.source_pdf_path.name,
            "char_count": len(content),
            "word_count": len(content.split()),
            "text": content
        }

        # Save to processed .jsonl
        with self.paths["processed_jsonl"].open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        # Save to processed .txt
        with self.paths["processed_txt"].open("a", encoding="utf-8") as f:
            f.write(content + "\n")

    def push_to_huggingface_hub(self):
        """
        Pushes the processed data (TXT and JSONL) to Hugging Face Hub.
        """
        try:
            existing_dataset = load_dataset(self.repo_id, split="train")
            existing_texts = existing_dataset["text"]
        except Exception:
            existing_texts = []

        new_lines = self.paths["upload_txt"].read_text(encoding="utf-8").splitlines()
        combined_dataset = Dataset.from_dict({"text": existing_texts + new_lines})
        combined_dataset.push_to_hub(self.repo_id, private=True)

        try:
            existing_jsonl_path = hf_hub_download(
                repo_id=self.repo_id,
                filename=self.paths["upload_jsonl"],
                repo_type="dataset"
            )
            with open(existing_jsonl_path, "r", encoding="utf-8") as f:
                existing_lines = [line.strip() for line in f if line.strip()]
        except Exception:
            print("Existing JSONL not found. Creating new.")
            existing_lines = []

        with self.paths["processed_jsonl"].open("r", encoding="utf-8") as f:
            new_lines = [line.strip() for line in f if line.strip()]

        all_lines = existing_lines + new_lines
        combined_jsonl = Path("combined_temp.jsonl")
        with combined_jsonl.open("w", encoding="utf-8") as f:
            for line in all_lines:
                f.write(line + "\n")

        upload_file(
            path_or_fileobj=combined_jsonl,
            path_in_repo=self.paths["upload_jsonl"],
            repo_id=self.repo_id,
            repo_type="dataset",
        )

        # After the upload is successful, delete the local file
        if combined_jsonl.exists():
            os.remove(combined_jsonl)
