# PDF to Mathpix Markdown Converter

This tool converts PDF files to Mathpix Markdown (.mmd) format using the Mathpix API with streaming support for faster results.

## Features

- Convert single PDFs or entire folders of PDFs to Mathpix Markdown
- Real-time streaming of conversion results for immediate feedback
- Progress tracking with detailed status information
- Automatic fallback to traditional download method if streaming fails
- Batch processing with overall progress tracking
- Support for mathematical notation with configurable delimiters

## Prerequisites

1. Python 3.6 or higher
2. A Mathpix API account (app_id and app_key)

## Installation

1. Clone this repository or download the `convert_pdf.py` script.

2. Install required dependencies:
   ```bash
   pip install httpx python-dotenv tqdm
   ```

3. Create a `.env` file in the same directory as the script with your Mathpix API credentials:
   ```
   MATHPIX_APP_ID=your_app_id
   MATHPIX_APP_KEY=your_app_key
   ```

## Usage

### Basic Usage

Convert a single PDF file:
```bash
python convert_pdf.py path/to/document.pdf
```

Convert all PDFs in a directory:
```bash
python convert_pdf.py path/to/folder/
```

### Command Line Options

```
python convert_pdf.py [-h] [-o OUT_DIR] [-v] [--skip-status-check] [--silent] input
```

- `input`: Path to PDF file or directory of PDFs (required)
- `-o, --out-dir`: Directory to write .mmd files (default: same as PDF folder)
- `-v, --verbose`: Enable detailed logging
- `--skip-status-check`: Skip final status check (use when all pages are received via streaming)
- `--silent`: Hide progress bars (only show log messages)

### Examples

Convert a PDF and save the output to a specific directory:
```bash
python convert_pdf.py document.pdf -o output/
```

Convert all PDFs in a directory with verbose logging:
```bash
python convert_pdf.py pdfs/ -v
```

Run a silent conversion without progress bars:
```bash
python convert_pdf.py document.pdf --silent
```

## How It Works

1. The script submits PDF files to the Mathpix API
2. It establishes a streaming connection to receive results in real-time
3. As pages are processed, they are immediately written to the output file
4. Progress is tracked and displayed via progress bars
5. If streaming fails, the script falls back to polling and downloading the complete file

## Customization

You can modify the `options` dictionary in the `async_main()` function to customize the conversion. Current defaults:

```python
options = {
    "math_inline_delimiters": ["$", "$"],
    "rm_spaces": True
}
```

See the [Mathpix API documentation](https://mathpix.com/docs/api/v3/pdf) for additional options [1].

## Troubleshooting

- **API Key Errors**: Ensure your `.env` file contains valid Mathpix API credentials
- **Timeout Errors**: For large PDFs, consider increasing timeout values in the code
- **Streaming Issues**: If streaming consistently fails, try using the `--skip-status-check` flag
