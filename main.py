from scripts.corpus_processor import CorpusProcessor

# 1. Extract text from the PDF and save it to 'data/raw/raw_kurmanji.txt'
processor = CorpusProcessor("data/data_files/file_name.pdf")

# 2. After manual review, append the data to the processed files
processor.finalize_and_save_processed_data()

# 3. Upload the data to the Hugging Face Hub
processor.push_to_huggingface_hub()
