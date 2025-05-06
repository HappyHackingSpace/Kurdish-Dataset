# Kurdish-Dataset

This repository aims to be a comprehensive dataset written in the Kurdish language, sourced from various materials. The resulting dataset will facilitate diverse studies on the Kurdish language.

## Table of Contents
- [Repository Contents](#repository-contents)
- [Installation](#installation)
- [Usage](#usage)
- [Data Integration Workflow](#data-integration-workflow)
- [Contributing](#contributing)
- [License](#license)

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
- **corpus_processor.py**: A script to convert files to text and push to Huggingface Hub.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Kurdish-Dataset.git
cd Kurdish-Dataset
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
Create a `.env` file in the root directory and add your Hugging Face token:
```
HUGGINGFACE_TOKEN=your_token_here
```

## Usage

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
5. Push the processed data to Hugging Face Hub:
   ```python
   processor.push_to_huggingface_hub()
   ```
   This will:
   - Upload the processed text to the Hugging Face Hub dataset
   - Merge the new JSONL data with any existing data on the Hub
   - Update both the text and JSONL files in the dataset
   - The dataset will be private and accessible only with proper authentication

### Customizing Page Ranges
The `CorpusProcessor` class supports two optional parameters: `start_page` and `end_page`. These parameters allow users to specify the range of pages to extract text from a PDF. By default, both parameters are `None`, meaning the entire PDF is processed. To process specific pages, specify the range as shown below:

```python
processor = CorpusProcessor("data/data_files/file_name.pdf", start_page=1, end_page=5)
```

## Contributing
We welcome contributions to this project! Here's how you can help:

1. Fork the repository
2. Create a new branch for your feature (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your contributions align with the project's goals and follow the established workflow.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.