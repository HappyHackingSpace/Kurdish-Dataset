import PyPDF2
import os

class CorpusProcessor:
    def __init__(self, file_path):
        self.file_path = file_path

    def extract_text_only(self):
        """
        PDF dosyasından sadece metni çıkarır
        """
        try:
            with open(self.file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            print(f"PDF işlenirken hata oluştu: {str(e)}")
            return "" 