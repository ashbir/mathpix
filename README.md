# Mathpix PDF Converter

A Python command-line tool for batch-converting PDFs to Mathpix Markdown using the Mathpix API with streaming support.

## Features

- **PDF Conversion**: Convert PDF files to Mathpix Markdown (.mmd) format
- **Batch Processing**: Process entire directories of PDFs in one command
- **Streaming Support**: Stream conversion results in real-time for faster output
- **Filename Anonymization**: Protect your privacy by anonymizing filenames sent to Mathpix
- **Image Handling**: Automatically downloads images from Mathpix CDN referenced in MMD, `lines.json`, and `lines.mmd.json` files, updating links to local paths.
- **Document Management**: List, download, and delete documents stored on the Mathpix server

## Requirements

- Python 3.7+
- A Mathpix API key ([sign up here](https://mathpix.com/))

## Installation

1. Clone this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

Alternatively, you can install the required packages manually:

```bash
pip install httpx tqdm python-dotenv requests beautifulsoup4
```

3. Create a `.env` file in the project directory with your Mathpix credentials:

```
MATHPIX_APP_ID=your_app_id
MATHPIX_APP_KEY=your_app_key
```

## Usage

The script offers a range of functionalities, from basic PDF conversion to detailed document management on the Mathpix server. CLI arguments are organized into logical groups for clarity. To see all available options and their groupings, run:

```bash
python convert_pdf.py --help
```

### Basic PDF Conversion

Convert a single PDF to Mathpix Markdown (.mmd):
```bash
python convert_pdf.py /path/to/your.pdf
```

Convert all PDFs in a directory:
```bash
python convert_pdf.py /path/to/your_directory/
```

Specify an output directory for the converted files:
```bash
python convert_pdf.py /path/to/your.pdf -o /output/directory/
# or
python convert_pdf.py /path/to/your.pdf --out-dir /output/directory/
```

### Conversion Control

Control various aspects of the PDF conversion process.

**Anonymizing Filenames:**
Filenames sent to Mathpix can be anonymized. This is controlled by the `--anonymize` option (default is `hash`).
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

**Image Handling in Conversion:**
By default, the Mathpix API includes image data in the generated MMD. You can prevent this:
```bash
# Do not include images in the output MMD from the Mathpix API
python convert_pdf.py /path/to/your.pdf --no-images
```

**Streaming and Status Checks:**
- Use streaming for faster real-time results (default is True, use `--use-streaming false` to disable).
- Skip the final status check after streaming (can speed up processing if you trust the stream):
```bash
python convert_pdf.py /path/to/your.pdf --skip-status-check
```

### Document Management (Mathpix API)

Manage your documents on the Mathpix server.

**List Documents:**
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

**Download Documents:**
Download a previously processed document from Mathpix by its PDF ID:
```bash
python convert_pdf.py --download-document YOUR_PDF_ID
```
Download in a specific format (default is `mmd`):
```bash
python convert_pdf.py --download-document YOUR_PDF_ID --output-format docx
```
Available download formats: `mmd`, `md`, `docx`, `tex.zip`, `pdf`, `latex.pdf`, `html`, `lines.json`, `lines.mmd.json`.
Specify an output path for the downloaded document:
```bash
python convert_pdf.py --download-document YOUR_PDF_ID --output-format docx --output-path ~/Downloads/document.docx
```
Note: When downloading `mmd`, `lines.json`, or `lines.mmd.json` formats, if the `--download-images` flag (see Local File Utilities) is active (default), images referenced in these files will be downloaded locally, and paths updated.

**Delete Documents:**
```bash
python convert_pdf.py --delete-document YOUR_PDF_ID
```

**Existence Check:**
By default, the script checks if a document with the same anonymized name already exists on Mathpix to avoid re-processing. You can skip this:
```bash
python convert_pdf.py /path/to/your.pdf --skip-existence-check
```

### Local File Utilities

Utilities for managing local files related to the conversion process.

**Check Anonymized Filename:**
See what the anonymized filename for a PDF would be without processing:
```bash
python convert_pdf.py --check-hash /path/to/your.pdf
```

**Local Image Downloading:**
After an MMD, `lines.json`, or `lines.mmd.json` file is created (either via conversion or download), this tool can download images referenced in it from the Mathpix CDN to a local directory (e.g., `your_file.mmd` images go into `your_file/` subdirectory) and update the links within the document. This is enabled by default.
```bash
# Disable automatic local image downloading and link updating
python convert_pdf.py /path/to/your.pdf --download-images false
```
This option also applies when using `--download-document` for relevant formats.

### Logging & Display

Control the script's output verbosity.

Enable verbose logging:
```bash
python convert_pdf.py /path/to/your.pdf -v
# or
python convert_pdf.py /path/to/your.pdf --verbose
```

Hide progress bars and most non-error output (useful for scripting):
```bash
python convert_pdf.py /path/to/your.pdf --silent
```

## How It Works

This tool:

1. Uploads PDFs to the Mathpix API
2. Optionally anonymizes filenames for privacy
3. Uses streaming to receive results page-by-page in real-time
4. Writes Mathpix Markdown (.mmd) output files
5. Downloads images referenced in MMD or supported JSON formats (like `lines.json`, `lines.mmd.json`), updates the documents to use local image paths, and stores images in a subdirectory named after the source file.
6. Can manage documents stored on the Mathpix server

## Troubleshooting

- Ensure your `.env` file exists with valid Mathpix credentials
- Check your network connection to api.mathpix.com
- For large PDFs, the conversion might take several minutes
- When deleting documents, they may still appear in listings for a few minutes due to server-side caching

## License

See the LICENSE file for details.
