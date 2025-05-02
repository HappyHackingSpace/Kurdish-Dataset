import re
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from pdfminer.layout import LAParams
import os
import json

class PDFTextExtractor:
    def __init__(self, pdf_path, start_page=None, end_page=None):
        """
        Initializes the PDFTextExtractor class and immediately processes the PDF.

        Args:
            pdf_path (str): Path to the PDF file.
            start_page (int, optional): Starting page (1-indexed). Defaults to None.
            end_page (int, optional): Ending page (inclusive, 1-indexed). Defaults to None.
        """
        self.pdf_path = pdf_path
        self.start_page = start_page
        self.end_page = end_page
        self.raw_file_path = "data/raw/raw_kurmanji.txt"
        self.processed_txt_path = "data/processed/kurmanji.txt"
        self.processed_json_path = "data/processed/kurmanji.json"

        # Extract and save text upon initialization
        self.cleaned_text = self.extract_text()
        self.save_to_raw(self.cleaned_text)

    def extract_text(self):
        """
        Extracts and cleans text from the PDF file.

        Returns:
            str: Cleaned text extracted from the PDF.
        """
        text = ""
        page_range = None

        # Define page range if specified
        if self.start_page and self.end_page:
            page_range = range(self.start_page - 1, self.end_page)  # Zero-indexed

        # Extract text from specified pages or entire PDF
        laparams = LAParams()
        for page_layout in extract_pages(self.pdf_path, page_numbers=page_range, laparams=laparams):
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text += element.get_text()

        # Clean the extracted text
        cleaned_text = re.sub(r'[^\w\s\.,\']+', '', text).replace('\n', ' ').strip()
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        # Add a new line after each period unless it's part of ".." or "..."
        cleaned_text = re.sub(r'(?<!\.)\.\s+', '.\n', cleaned_text)

        return cleaned_text

    def save_to_raw(self, text, mode="w"):
        """
        Appends the cleaned text to the raw file.

        Args:
            text (str): Text to be saved.
            mode (str): The mode of writing. "w" for overwriting, "a" for appending. Default is "w".
        """
        with open(self.raw_file_path, mode, encoding="utf-8") as file:
            file.write(text + "\n")
    def append_raw_to_processed_data(self):
        """
        Reads text from the raw file and appends it as a single JSON line to a .jsonl file,
        and also appends the raw text to the processed .txt file.
        """
        with open(self.raw_file_path, "r", encoding="utf-8") as raw_file:
            content = raw_file.read().strip()

        char_count = len(content)
        word_count = len(content.split())

        record = {
            "file_name": os.path.basename(self.pdf_path),
            "char_count": char_count,
            "word_count": word_count,
            "text": content
        }

        with open(self.processed_json_path, "a", encoding="utf-8") as jsonl_file:
            jsonl_file.write(json.dumps(record, ensure_ascii=False) + "\n")

        # 4) Processed .txt dosyasına da ekle
        with open(self.processed_txt_path, "a", encoding="utf-8") as processed_file:
            processed_file.write(content + "\n")
