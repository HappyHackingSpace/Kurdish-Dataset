# Kurdish-Dataset

This repository aims to be a comprehensive dataset written in the Kurdish language, sourced from various materials. The resulting dataset will facilitate diverse studies on the Kurdish language.

## Repository Contents

### Data Directory
The `data` folder is the main container for dataset-related files. It is organized into three subfolders:

- **data_files**: Contains data tables (e.g., PDFs) to be added to the dataset.
- **raw**: Serves as a backup folder. It includes:
  - `raw_kurmanji.txt`: Stores unprocessed text extracted using the `CorpusProcessor` from `corpus_processor.py`. This file is used for manual review and corrections before processing.
- **processed**: The final output folder, containing:
  - `kurmanji.txt`: The plain text file of the final dataset.
  - `kurmanji.json`: The JSON representation of the final dataset, automatically populated with the following fields:
    - `file_name`: The source file name.
    - `char_count`: The character count of the text.
    - `word_count`: The word count of the text.
    - `text`: The actual text content.

### Scripts Directory
The `scripts` folder contains:
- **corpus_processor.py**: A script to convert PDF files to text and push Huggingface Hub.

### Main Script
`main.py` is the primary Python script, enabling streamlined data integration without dealing directly with intermediate processing scripts. Below is an example usage:

```python
from scripts.corpus_processor import CorpusProcessor

# 1. Extract text from the PDF and save it to 'data/raw/raw_kurmanji.txt'
processor = CorpusProcessor("data/data_files/file_name.pdf")

# 2. After manual review, append the data to the processed files
processor.finalize_and_save_processed_data()

# 3. Upload the data to the Hugging Face Hub
processor.push_to_huggingface_hub()
```

## Data Integration Workflow
1. Add the desired file to the `data/data_files` directory.
2. Use the `CorpusProcessor` class to extract raw text:
   ```python
   processor = CorpusProcessor("data/data_files/file_name.pdf")
   ```
   The extracted text will be saved in `data/raw/raw_kurmanji.txt` for manual review.
3. Manually review and correct the contents of `data/raw/raw_kurmanji.txt`.
4. Transfer the reviewed data to the processed files:
   ```python
   processor.finalize_and_save_processed_data()
   ```
   The reviewed data will be appended to `data/processed/kurmanji.txt` and `data/processed/kurmanji.json`.

### Customizing Page Ranges
The `CorpusProcessor` class supports two optional parameters: `start_page` and `end_page`. These parameters allow users to specify the range of pages to extract text from a PDF. By default, both parameters are `None`, meaning the entire PDF is processed. To process specific pages, specify the range as shown below:

```python
processor = CorpusProcessor("data/data_files/file_name.pdf", start_page=1, end_page=5)
```