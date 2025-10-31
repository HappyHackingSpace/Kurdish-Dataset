import PyPDF2

class CorpusProcessor:
    def __init__(self, file_path):
        self.file_path = file_path

    def extract_text_only(self):
        try:
            with open(self.file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            print(f"Error: {str(e)}")
            return "" 