# Mathpix PDF Converter

A Python command-line tool for batch-converting PDFs to Mathpix Markdown using the Mathpix API with streaming support.

## Features

- **PDF Conversion**: Convert PDF files to Mathpix Markdown (.mmd) format
- **Batch Processing**: Process entire directories of PDFs in one command
- **Streaming Support**: Stream conversion results in real-time for faster output
- **Filename Anonymization**: Protect your privacy by anonymizing filenames sent to Mathpix
- **Document Management**: List and delete documents stored on the Mathpix server

## Requirements

- Python 3.7+
- A Mathpix API key ([sign up here](https://mathpix.com/))

## Installation

1. Clone this repository
2. Install dependencies:

```bash
pip install httpx tqdm python-dotenv
```

3. Create a `.env` file in the project directory with your Mathpix credentials:

```
MATHPIX_APP_ID=your_app_id
MATHPIX_APP_KEY=your_app_key
```

## Usage

### Converting PDFs

Convert a single PDF:

```bash
python convert_pdf.py /path/to/your.pdf
```

Convert all PDFs in a directory:

```bash
python convert_pdf.py /path/to/directory/
```

Specify an output directory:

```bash
python convert_pdf.py /path/to/your.pdf -o /output/directory/
```

### Anonymizing Filenames

Filenames are anonymized by default using MD5 hash to allow tracking. You can change the anonymization method:

```bash
# Hash-based anonymization (default) - consistent names for the same file
python convert_pdf.py document.pdf --anonymize hash

# UUID-based anonymization - random unique names each time
python convert_pdf.py document.pdf --anonymize uuid

# Simple timestamp-based anonymization
python convert_pdf.py document.pdf --anonymize simple

# Disable anonymization
python convert_pdf.py document.pdf --anonymize none
```

Check what an anonymized filename would be:

```bash
python convert_pdf.py --check-hash /path/to/your.pdf
```

### Document Management

List documents stored on the Mathpix server:

```bash
python convert_pdf.py --list-documents
```

Use pagination for large document lists:

```bash
python convert_pdf.py --list-documents --page 2 --per-page 50
```

Filter documents by date:

```bash
python convert_pdf.py --list-documents --from-date 2023-01-01 --to-date 2023-12-31
```

Delete a document from the Mathpix server:

```bash
python convert_pdf.py --delete-document YOUR_PDF_ID
```

### Advanced Options

Enable verbose logging:

```bash
python convert_pdf.py /path/to/your.pdf -v
```

Skip final status check (faster processing when using streaming):

```bash
python convert_pdf.py /path/to/your.pdf --skip-status-check
```

Hide progress bars (useful for scripts):

```bash
python convert_pdf.py /path/to/your.pdf --silent
```

## How It Works

This tool:

1. Uploads PDFs to the Mathpix API
2. Optionally anonymizes filenames for privacy
3. Uses streaming to receive results page-by-page in real-time  
4. Writes Mathpix Markdown (.mmd) output files
5. Can manage documents stored on the Mathpix server

## Troubleshooting

- Ensure your `.env` file exists with valid Mathpix credentials
- Check your network connection to api.mathpix.com
- For large PDFs, the conversion might take several minutes
- When deleting documents, they may still appear in listings for a few minutes due to server-side caching

## License

See the LICENSE file for details.
