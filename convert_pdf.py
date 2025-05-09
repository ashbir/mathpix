#!/usr/bin/env python3
import os
import json
import argparse
import asyncio
import httpx
import traceback
import logging
import time
import sys
import hashlib
import uuid
import re
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv
from tqdm import tqdm
from typing import Dict, List, Tuple, Optional, Any, Union

# Configure a null handler by default
logging.getLogger().addHandler(logging.NullHandler())

def anonymize_filename(original_path: str, anonymize_method: str = 'hash') -> str:
    """Generate an anonymized filename for PDFs sent to Mathpix
    
    Args:
        original_path: The original file path
        anonymize_method: Method to use for anonymization ('hash', 'uuid', or 'simple')
    
    Returns:
        An anonymized filename with the .pdf extension preserved
    """
    # Extract the extension
    _, ext = os.path.splitext(original_path)
    
    # Generate anonymized name based on selected method
    if anonymize_method == 'uuid':
        # Use UUID to generate a random unique identifier
        anonymized_name = f"doc_{str(uuid.uuid4())[:8]}{ext}"
    elif anonymize_method == 'hash':
        # Generate a hash from the original filename
        filename = os.path.basename(original_path)
        hash_obj = hashlib.md5(filename.encode())
        anonymized_name = f"doc_{hash_obj.hexdigest()[:8]}{ext}"
    elif anonymize_method == 'simple':
        # Just use a simple numbered format
        timestamp = int(time.time())
        anonymized_name = f"document_{timestamp}{ext}"
    else:
        # Default fallback to hash
        filename = os.path.basename(original_path)
        hash_obj = hashlib.md5(filename.encode())
        anonymized_name = f"doc_{hash_obj.hexdigest()[:8]}{ext}"
        
    return anonymized_name

def get_anonymized_filename(file_path: str, method: str = 'hash') -> str:
    """Compute and return the anonymized filename for a file without actually renaming it.
    
    This function is useful to check what the hash name would be for a given PDF file,
    helping track which file corresponds to which file on the Mathpix server.
    
    Args:
        file_path: Path to the file
        method: Anonymization method ('hash', 'uuid', or 'simple')
        
    Returns:
        The anonymized filename that would be used when uploading to Mathpix
    """
    return anonymize_filename(file_path, method)

# Add function to download images from Mathpix CDN
def download_mathpix_image(url: str, output_dir: str) -> str:
    """
    Download an image from a Mathpix CDN URL and save it to the output directory.
    
    Args:
        url: The URL of the image to download
        output_dir: The directory to save the image to
        
    Returns:
        The path to the saved image
    """
    try:
        # Clean URL by properly handling backslashes in query parameters
        url = url.replace('\\&', '&')
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse the URL to extract information for the filename
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')
        filename = path_parts[-1]
        
        # Extract parameters for a more descriptive filename
        query_params = {}
        if parsed_url.query:
            for param in parsed_url.query.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    query_params[key] = value

        # Create a descriptive filename based on URL parameters
        if 'top_left_x' in query_params and 'top_left_y' in query_params and 'width' in query_params and 'height' in query_params:
            base_name = os.path.splitext(filename)[0]
            ext = os.path.splitext(filename)[1]
            new_filename = f"{base_name}_x{query_params['top_left_x']}_y{query_params['top_left_y']}_w{query_params['width']}_h{query_params['height']}{ext}"
        elif 'height' in query_params:
            # Special case for lines.json and lines.mmd.json format images from Mathpix
            base_name = os.path.splitext(filename)[0]
            ext = os.path.splitext(filename)[1]
            new_filename = f"{base_name}_h{query_params['height']}{ext}"
        else:
            new_filename = filename

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the image to the output directory
        image_path = os.path.join(output_dir, new_filename)
        with open(image_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Downloaded image: {url} -> {image_path}")
        return image_path
        
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return None

def extract_and_download_mathpix_images(content, output_dir, pattern=None):
    """
    Common function to extract and download Mathpix CDN images from content.
    
    Args:
        content: The content to search for image URLs (string for markdown, dict for JSON)
        output_dir: Directory to save downloaded images
        pattern: Regular expression pattern to match image URLs (if None, uses default)
        
    Returns:
        list: List of downloaded image paths
    """
    # Use default pattern if none provided
    if pattern is None:
        pattern = r'https?://cdn\.mathpix\.com/cropped/[^)"\'\\s]+'
    
    downloaded_images = []
    
    # Handle JSON content
    if isinstance(content, dict):
        # Process lines.mmd.json format - has pages with lines that contain text fields
        if 'pages' in content and isinstance(content['pages'], list):
            for page in content['pages']:
                if 'lines' in page and isinstance(page['lines'], list):
                    for line in page['lines']:
                        if 'text' in line and isinstance(line['text'], str):
                            # Extract all Mathpix CDN URLs from the text
                            urls = re.findall(pattern, line['text'])
                            for url in urls:
                                # Clean up URL if it contains escape characters or quotes
                                cleaned_url = url.strip('"\\\'"')
                                local_image_path = download_mathpix_image(cleaned_url, output_dir)
                                if local_image_path:
                                    downloaded_images.append(local_image_path)
        
        # Recursively search for URLs in any field in the JSON
        def search_json_for_urls(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str):
                        urls = re.findall(pattern, value)
                        for url in urls:
                            cleaned_url = url.strip('"\\\'"')
                            local_image_path = download_mathpix_image(cleaned_url, output_dir)
                            if local_image_path:
                                downloaded_images.append(local_image_path)
                    else:
                        search_json_for_urls(value)
            elif isinstance(obj, list):
                for item in obj:
                    search_json_for_urls(item)
        
        # Search the entire JSON for any URLs we might have missed
        search_json_for_urls(content)
    
    # Handle string content (markdown)
    elif isinstance(content, str):
        # For markdown, we use a slightly different pattern that includes alt text
        md_pattern = r'!\[(.*?)\]\((https?://cdn\.mathpix\.com/cropped/.*?)\)'
        
        # Extract all Mathpix CDN URLs from the text
        matches = re.findall(md_pattern, content)
        for match in matches:
            # The URL is the second capture group
            image_url = match[1]
            # Download the image
            local_image_path = download_mathpix_image(image_url, output_dir)
            if local_image_path:
                downloaded_images.append(local_image_path)
    
    return downloaded_images

# Add function to process a markdown file and download images
def process_markdown_images(file_path: str, download_images: bool = True):
    """
    Process a markdown file to download images and update image references.
    
    Args:
        file_path: Path to the markdown file
        download_images: Whether to download images (default: True)
        
    Returns:
        Number of images processed
    """
    if not download_images:
        return 0
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get the filename without extension to use as the image directory name
        file_basename = os.path.basename(file_path)
        file_name_without_ext = os.path.splitext(file_basename)[0]
        
        # Create directory with the same name as the markdown file
        output_dir = os.path.join(os.path.dirname(file_path), file_name_without_ext)
        os.makedirs(output_dir, exist_ok=True)
        
        # Pattern to find image references in markdown format: ![alt text](image_url)
        image_pattern = r'!\[(.*?)\]\((https?://cdn\.mathpix\.com/cropped/.*?)\)'
        
        def download_and_replace(match):
            alt_text = match.group(1)
            image_url = match.group(2)
            
            # Download the image directly
            local_image_path = download_mathpix_image(image_url, output_dir)
            
            if local_image_path:
                # Get relative path from markdown file to image
                rel_path = os.path.relpath(local_image_path, os.path.dirname(file_path))
                return f'![{alt_text}]({rel_path})'
            else:
                # If download failed, keep the original link
                return match.group(0)
        
        # Find all matches and count them
        matches = re.findall(image_pattern, content)
        image_count = len(matches)
        
        if image_count > 0:
            # Replace all image URLs with local paths and download in a single pass
            updated_content = re.sub(image_pattern, download_and_replace, content)
            
            # Save updated content back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            logger.info(f"Updated {image_count} image links in {file_path}")
        
        return image_count
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return 0

def process_json_images(file_path: str) -> int:
    """
    Process a JSON file to extract and download images from Mathpix CDN URLs.
    This handles both lines.json and lines.mmd.json formats from Mathpix.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Number of images processed
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        # Get the filename without extension to use as the image directory name
        file_basename = os.path.basename(file_path)
        file_name_without_ext = os.path.splitext(file_basename)[0]
        if file_name_without_ext.endswith('.lines'):
            file_name_without_ext = file_name_without_ext[:-6]  # Remove '.lines' suffix
        
        # Create directory with the same name as the JSON file
        output_dir = os.path.join(os.path.dirname(file_path), file_name_without_ext)
        os.makedirs(output_dir, exist_ok=True)
        
        # Regular expression pattern to find Mathpix CDN image URLs
        pattern = r'(https?://cdn\.mathpix\.com/cropped/[^)"\'\\s]+)'
        # Pattern to find image references in markdown format within JSON strings
        md_pattern = r'!\[(.*?)\]\((https?://cdn\.mathpix\.com/cropped/.*?)\)'
        
        # Track all downloaded images and their mappings
        downloaded_images = {}  # Original URL -> local path
        replacement_count = 0
        
        # Process the content based on its structure
        if isinstance(content, dict) and 'pages' in content:
            # For both lines.json and lines.mmd.json formats
            for page in content['pages']:
                if 'lines' in page and isinstance(page['lines'], list):
                    for line in page['lines']:
                        # Process 'text' field which can contain markdown image syntax
                        if 'text' in line and isinstance(line['text'], str):
                            # Find all markdown image patterns
                            matches = re.findall(md_pattern, line['text'])
                            for match in matches:
                                alt_text = match[0]
                                image_url = match[1]
                                
                                # Download the image if not already downloaded
                                if image_url not in downloaded_images:
                                    local_path = download_mathpix_image(image_url, output_dir)
                                    if local_path:
                                        downloaded_images[image_url] = local_path
                                
                                # Replace URL with local path
                                if image_url in downloaded_images:
                                    local_path = downloaded_images[image_url]
                                    rel_path = os.path.relpath(local_path, os.path.dirname(file_path))
                                    line['text'] = line['text'].replace(
                                        f'![{alt_text}]({image_url})', 
                                        f'![{alt_text}]({rel_path})'
                                    )
                                    replacement_count += 1
                            
                            # Also find and replace any raw URLs (not in markdown syntax)
                            raw_urls = re.findall(pattern, line['text'])
                            for url in raw_urls:
                                # Skip URLs already handled by markdown pattern
                                if any(url == match[1] for match in matches):
                                    continue
                                
                                # Download the image if not already downloaded
                                if url not in downloaded_images:
                                    local_path = download_mathpix_image(url, output_dir)
                                    if local_path:
                                        downloaded_images[url] = local_path
                                
                                # Replace URL with local path
                                if url in downloaded_images:
                                    local_path = downloaded_images[url]
                                    rel_path = os.path.relpath(local_path, os.path.dirname(file_path))
                                    line['text'] = line['text'].replace(url, rel_path)
                                    replacement_count += 1
                        
                        # For lines.json format, also check 'text_display' field
                        if 'text_display' in line and isinstance(line['text_display'], str):
                            # Find all markdown image patterns
                            matches = re.findall(md_pattern, line['text_display'])
                            for match in matches:
                                alt_text = match[0]
                                image_url = match[1]
                                
                                # Download the image if not already downloaded
                                if image_url not in downloaded_images:
                                    local_path = download_mathpix_image(image_url, output_dir)
                                    if local_path:
                                        downloaded_images[image_url] = local_path
                                
                                # Replace URL with local path
                                if image_url in downloaded_images:
                                    local_path = downloaded_images[image_url]
                                    rel_path = os.path.relpath(local_path, os.path.dirname(file_path))
                                    line['text_display'] = line['text_display'].replace(
                                        f'![{alt_text}]({image_url})', 
                                        f'![{alt_text}]({rel_path})'
                                    )
                                    replacement_count += 1
                            
                            # Also find and replace any raw URLs (not in markdown syntax)
                            raw_urls = re.findall(pattern, line['text_display'])
                            for url in raw_urls:
                                # Skip URLs already handled by markdown pattern
                                if any(url == match[1] for match in matches):
                                    continue
                                
                                # Download the image if not already downloaded
                                if url not in downloaded_images:
                                    local_path = download_mathpix_image(url, output_dir)
                                    if local_path:
                                        downloaded_images[url] = local_path
                                
                                # Replace URL with local path
                                if url in downloaded_images:
                                    local_path = downloaded_images[url]
                                    rel_path = os.path.relpath(local_path, os.path.dirname(file_path))
                                    line['text_display'] = line['text_display'].replace(url, rel_path)
                                    replacement_count += 1

        # Write the updated content back to the file
        if downloaded_images:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2)
            
            logger.info(f"Updated {replacement_count} image links in {file_path}")
            logger.info(f"Downloaded {len(downloaded_images)} images from {file_path}")
        
        return len(downloaded_images)
        
    except Exception as e:
        logger.error(f"Error processing JSON file {file_path}: {e}")
        return 0

class ConditionalLogger:
    """Custom logger that respects verbose flag"""
    def __init__(self, name, verbose=False):
        self.logger = logging.getLogger(name)
        self.verbose = verbose
        
        # Setup console handler if verbose
        if verbose:
            self.handler = logging.StreamHandler()
            self.handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(self.handler)
            self.logger.setLevel(logging.INFO)
    
    def set_verbose(self, verbose):
        self.verbose = verbose
        if verbose and not self.logger.handlers:
            self.handler = logging.StreamHandler()
            self.handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(self.handler)
            self.logger.setLevel(logging.INFO)
        elif not verbose and self.logger.handlers:
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)
    
    def set_level(self, level):
        if self.verbose:
            self.logger.setLevel(level)
    
    def debug(self, msg, *args, **kwargs):
        if self.verbose:
            self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        if self.verbose:
            self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        if self.verbose:
            self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        # Always log errors
        print(f"Error: {msg}", file=sys.stderr)
        if self.verbose:
            self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        # Always log critical errors
        print(f"Critical: {msg}", file=sys.stderr)
        if self.verbose:
            self.logger.critical(msg, *args, **kwargs)

# Initialize the conditional logger
logger = ConditionalLogger("mathpix_converter", verbose=False)

class MathpixClient:
    """Client for interacting with the Mathpix API"""
    
    BASE_URL = "https://api.mathpix.com/v3"
    PDF_ENDPOINT = f"{BASE_URL}/pdf"
    PDF_RESULTS_ENDPOINT = f"{BASE_URL}/pdf-results"
    
    def __init__(self, app_id: str, app_key: str):
        self.headers = {"app_id": app_id, "app_key": app_key}
        self.default_timeout = 120.0  # seconds
        
    async def submit_pdf(self, pdf_path: str, options: Dict[str, Any], anonymize_method: str = 'hash') -> Dict[str, Any]:
        """Submit a PDF file to the Mathpix API and return the response
        
        Args:
            pdf_path: Path to the PDF file
            options: Dictionary of options for Mathpix
            anonymize_method: Method to anonymize filename ('hash', 'uuid', 'simple', or 'none')
        
        Returns:
            Dictionary containing the Mathpix API response
        """
        pdf_name = os.path.basename(pdf_path)
        logger.info(f"[{pdf_name}] Submitting PDF...")
        logger.debug(f"[{pdf_name}] POST request with options: {options}")
        
        async with httpx.AsyncClient(timeout=self.default_timeout) as client:
            with open(pdf_path, "rb") as f:
                # Determine if we should anonymize
                if anonymize_method and anonymize_method.lower() != 'none':
                    # Anonymize the filename
                    anonymized_name = anonymize_filename(pdf_path, anonymize_method)
                    logger.info(f"[{pdf_name}] Using anonymized filename: {anonymized_name}")
                    files = {"file": (anonymized_name, f, "application/pdf")}
                else:
                    # Use original filename
                    files = {"file": f}
                
                data = {"options_json": json.dumps(options)}
                
                resp = await client.post(
                    self.PDF_ENDPOINT,
                    headers=self.headers,
                    files=files,
                    data=data
                )
            
            logger.debug(f"HTTP Request: POST {self.PDF_ENDPOINT} \"{resp.status_code} {resp.reason_phrase}\"")
            resp.raise_for_status()
            response_json = resp.json()
            logger.debug(f"[{pdf_name}] Submit response: {response_json}")
            
            return response_json
            
    async def get_pdf_status(self, pdf_id: str, pdf_name: str = "PDF") -> Dict[str, Any]:
        """Get the status of a PDF conversion"""
        status_url = f"{self.PDF_ENDPOINT}/{pdf_id}"
        logger.debug(f"[{pdf_name}] Checking status at {status_url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(status_url, headers=self.headers)
            logger.debug(f"HTTP Request: GET {status_url} \"{resp.status_code} {resp.reason_phrase}\"")
            resp.raise_for_status()
            status_data = resp.json()
            
            return status_data
    
    async def download_mmd(self, pdf_id: str, pdf_name: str = "PDF") -> str:
        """Download the MMD content for a converted PDF"""
        mmd_url = f"{self.PDF_ENDPOINT}/{pdf_id}.mmd"
        logger.info(f"[{pdf_name}] Downloading MMD from {mmd_url}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(mmd_url, headers=self.headers)
            logger.debug(f"HTTP Request: GET {mmd_url} \"{resp.status_code} {resp.reason_phrase}\"")
            
            if resp.status_code == 404:
                logger.error(f"[{pdf_name}] MMD file not available yet (404)")
                return ""
                
            resp.raise_for_status()
            return resp.text
    
    async def stream_pdf_results(self, pdf_id: str, pdf_name: str = "PDF") -> httpx.Response:
        """Get a streaming connection for real-time PDF conversion results
        
        Returns the response object directly rather than an AsyncGeneratorContextManager
        """
        stream_url = f"{self.PDF_ENDPOINT}/{pdf_id}/stream"
        logger.debug(f"[{pdf_name}] Establishing stream connection to {stream_url}")
        
        # Create client with longer timeout for streaming
        client = httpx.AsyncClient(timeout=300.0)
        
        # Get the response directly
        resp = await client.get(stream_url, headers=self.headers)
        logger.debug(f"HTTP Request: GET {stream_url} \"{resp.status_code} {resp.reason_phrase}\"")
        resp.raise_for_status()
        
        # The client needs to stay open for the stream to work, so attach it to the response
        # to prevent it from being garbage collected
        resp._client = client
        
        return resp
    
    async def list_documents(self, per_page: int = 100, page: int = 1, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Dict[str, Any]:
        """List all documents stored on the Mathpix server
        
        Args:
            per_page: Number of results to return per page
            page: Page number to retrieve
            from_date: Optional ISO format start date (e.g., "2023-01-01T00:00:00.000Z")
            to_date: Optional ISO format end date
            
        Returns:
            Dictionary containing the list of documents
        """
        logger.info(f"Retrieving document list (page {page}, {per_page} per page)")
        
        params = {
            "per_page": per_page,
            "page": page
        }
        
        if from_date:
            params["from_date"] = from_date
        
        if to_date:
            params["to_date"] = to_date
        
        async with httpx.AsyncClient(timeout=self.default_timeout) as client:
            resp = await client.get(
                self.PDF_RESULTS_ENDPOINT,
                headers=self.headers,
                params=params
            )
            
            logger.debug(f"HTTP Request: GET {self.PDF_RESULTS_ENDPOINT} \"{resp.status_code} {resp.reason_phrase}\"")
            resp.raise_for_status()
            return resp.json()

    async def document_exists(self, pdf_id: str) -> bool:
        """Check if a document with the given ID exists on the Mathpix server
        
        Args:
            pdf_id: The ID of the PDF document to check
            
        Returns:
            Boolean indicating if the document exists
        """
        logger.info(f"Checking if document exists with ID: {pdf_id}")
        
        url = f"{self.PDF_ENDPOINT}/{pdf_id}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                url,
                headers=self.headers
            )
            
            logger.debug(f"HTTP Request: GET {url} \"{resp.status_code} {resp.reason_phrase}\"")
            
            # Document exists if the status code is 200 OK
            return resp.status_code == 200
            
    async def delete_document(self, pdf_id: str) -> Dict[str, Any]:
        """Delete a document from the Mathpix server
        
        Args:
            pdf_id: The ID of the PDF document to delete
            
        Returns:
            Dictionary containing the response from the server
        """
        logger.info(f"Deleting document with ID: {pdf_id}")
        
        # First, check if the document exists
        document_exists = await self.document_exists(pdf_id)
        if not document_exists:
            logger.warning(f"Document with ID {pdf_id} not found")
            return {"success": False, "message": f"Document {pdf_id} not found on the Mathpix server"}
        
        url = f"{self.PDF_ENDPOINT}/{pdf_id}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.delete(
                url,
                headers=self.headers
            )
            
            logger.debug(f"HTTP Request: DELETE {url} \"{resp.status_code} {resp.reason_phrase}\"")
            
            # Check if the response body contains error information
            try:
                response_data = resp.json() if resp.content else {}
                if 'error' in response_data:
                    return {"success": False, "message": f"Server error: {response_data.get('error')}"}
            except:
                # Not JSON or parsing error
                pass
            
            # The Mathpix API returns 204 No Content for successful deletion
            # but may also return 200 OK in some cases
            if resp.status_code == 204 or resp.status_code == 200:
                # Additional check to verify the document was actually found and deleted
                # If we get a 200 OK but something went wrong, the response might have additional details
                if resp.content and len(resp.content) > 0:
                    try:
                        data = resp.json()
                        if data.get("status") == "error" or "error" in data:
                            error_msg = data.get("error", "Unknown error")
                            return {"success": False, "message": error_msg}
                    except:
                        # If we can't parse the response, assume it worked
                        pass
                
                return {"success": True, "message": f"Document {pdf_id} deleted successfully"}
            elif resp.status_code == 404:
                return {"success": False, "message": f"Document {pdf_id} not found"}
            
            # Handle other error status codes
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                return {"success": False, "message": f"HTTP error {e.response.status_code}: {e.response.text}"}
            
            # If the response contains JSON data, return it
            try:
                return resp.json()
            except:
                return {"success": False, "message": f"Unexpected response from server: {resp.text}"}

    async def download_document(self, pdf_id: str, output_format: str = "mmd", output_path: Optional[str] = None) -> str:
        """Download a document from the Mathpix server
        
        Args:
            pdf_id: The ID of the PDF document to download
            output_format: The format to download (mmd, md, docx, tex.zip, html, pdf, latex.pdf, lines.json, lines.mmd.json)
            output_path: Path to save the file (if None, will create a file using the original filename from server)
            
        Returns:
            Path to the downloaded file
        """
        logger.info(f"Downloading document with ID: {pdf_id} in format: {output_format}")
        
        # Check if the document exists and is completed
        try:
            status_data = await self.get_pdf_status(pdf_id, "Document")
            if status_data.get("status") != "completed":
                raise RuntimeError(f"Document {pdf_id} is not ready for download (status: {status_data.get('status')})")
        except Exception as e:
            raise RuntimeError(f"Failed to check document status: {e}")
        
        # Build the URL for the specific format
        url = f"{self.PDF_ENDPOINT}/{pdf_id}.{output_format}"
        
        # Determine file extension based on format
        if output_format == "tex":
            file_ext = "tex.zip"
        elif output_format == "lines.json" or output_format == "lines.mmd.json":
            file_ext = output_format
        else:
            file_ext = output_format
            
        # Try to find original filename from document listing if not provided in status data
        original_filename = None
        original_input_file = status_data.get("input_file", "")
        
        if not original_input_file or original_input_file == "Unknown":
            # Try to get document details from the document list
            try:
                logger.info(f"Looking up additional document information for {pdf_id}...")
                docs = await self.list_documents(per_page=100, page=1)
                
                if "pdfs" in docs and docs["pdfs"]:
                    for pdf in docs["pdfs"]:
                        if pdf.get("id") == pdf_id:
                            original_input_file = pdf.get("input_file", "")
                            logger.info(f"Found original file information: {original_input_file}")
                            break
            except Exception as e:
                logger.warning(f"Could not retrieve document list to find original filename: {e}")
        
        # Download the file
        logger.info(f"Downloading from {url}")
        
        async with httpx.AsyncClient(timeout=300.0) as client:  # Longer timeout for potentially large files
            resp = await client.get(url, headers=self.headers)
            
            logger.debug(f"HTTP Request: GET {url} \"{resp.status_code} {resp.reason_phrase}\"")
            
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to download document: HTTP {resp.status_code} - {resp.text}")
            
            # Binary formats need to be written in binary mode
            binary_formats = ["docx", "tex", "tex.zip", "pdf", "latex.pdf"]
            write_mode = "wb" if output_format in binary_formats else "w"
            
            # Get the original filename from the server if available in Content-Disposition header
            if 'Content-Disposition' in resp.headers:
                content_disp = resp.headers['Content-Disposition']
                # Look for filename="something.ext" or filename=something.ext in the header
                match = re.search(r'filename=["\']?([^"\';\n]+)', content_disp)
                if match:
                    content_disp_filename = match.group(1)
                    # Only use this if it's not just the PDF ID
                    if pdf_id not in content_disp_filename:
                        original_filename = content_disp_filename
                        logger.info(f"Found original filename in headers: {original_filename}")
                    else:
                        logger.info(f"Header filename {content_disp_filename} appears to be PDF ID, not using it")
            
            # If no filename from headers, try to extract from input_file field
            if not original_filename and original_input_file:
                # Extract just the filename part if it's a path or URL
                base_filename = os.path.basename(original_input_file)
                
                # If we found a base filename, use it
                if base_filename:
                    # Remove any existing extension and add the correct extension for the format
                    original_filename = os.path.splitext(base_filename)[0] + f".{file_ext}"
                    logger.info(f"Using filename from document information: {original_filename}")
            
            # Determine output path
            if output_path is None:
                if original_filename:
                    output_path = original_filename
                else:
                    output_path = f"{pdf_id}.{file_ext}"
                    logger.info(f"No original filename found, using PDF ID: {output_path}")
            
            logger.info(f"Saving to {output_path}")
            
            # Write the response content to the output file
            with open(output_path, write_mode) as f:
                if write_mode == "wb":
                    f.write(resp.content)
                else:
                    f.write(resp.text)
            
            logger.info(f"Document downloaded successfully to {output_path}")
            return output_path

class PDFConverter:
    """Handles the conversion of PDFs to Mathpix Markdown"""
    
    def __init__(self, client: MathpixClient, options: Dict[str, Any] = None, show_progress: bool = True):
        self.client = client
        self.options = options or {}
        self.show_progress = show_progress
        
    async def convert_with_streaming(self, pdf_path: str, out_path: str, anonymize_method: str = 'hash', download_images: bool = True) -> Tuple[str, int, int]:
        """
        Convert a PDF to MMD using streaming API
        
        Args:
            pdf_path: Path to the PDF file
            out_path: Path to save the output file
            anonymize_method: Method to anonymize filename
            download_images: Whether to download images from Mathpix CDN
            
        Returns:
            Tuple[str, int, int]: (pdf_id, pages_received, total_pages)
        """
        pdf_name = os.path.basename(pdf_path)
        
        # Add streaming option
        options = {**self.options, "streaming": True}
        
        try:
            # 1. Submit PDF
            response = await self.client.submit_pdf(pdf_path, options, anonymize_method)
            pdf_id = response["pdf_id"]
            logger.info(f"[{pdf_name}] submitted → pdf_id={pdf_id}")
            
            # 2. Stream results and write to file incrementally
            result = await self._handle_streaming(pdf_id, pdf_name, out_path)
            
            # 3. Download images if requested
            if download_images:
                logger.info(f"[{pdf_name}] Downloading images from MMD file")
                if not self.show_progress:
                    # Show minimal message if not verbose
                    print(f"Downloading images for {pdf_name}...")
                
                # Process the markdown file to download images
                image_count = process_markdown_images(out_path, download_images)
                
                # Also process any conversion formats specified in options
                if "conversion_formats" in self.options and self.options["conversion_formats"]:
                    conversion_formats = self.options["conversion_formats"]
                    for format_key, enabled in conversion_formats.items():
                        if not enabled:
                            continue
                        
                        # Get the format extension (.md, .docx, etc.)
                        format_ext = format_key
                        
                        # Process images for any markdown-based formats
                        if format_ext in ["md"]:
                            format_path = os.path.splitext(out_path)[0] + f".{format_ext}"
                            # Wait for the conversion to complete
                            await self._wait_for_format_completion(pdf_id, format_ext)
                            
                            # If the file exists, process images
                            if os.path.exists(format_path):
                                logger.info(f"[{pdf_name}] Processing images in {format_ext} output")
                                process_markdown_images(format_path, download_images)
                
                if not self.show_progress and image_count > 0:
                    # Show minimal success message if not verbose
                    print(f"✅ Downloaded {image_count} images for {pdf_name}")
            
            return result
                    
        except Exception as e:
            logger.error(f"[{pdf_name}] Conversion failed: {e}")
            logger.error(traceback.format_exc())
            
            # If we have a pdf_id but streaming failed, we can fall back
            if 'pdf_id' in locals():
                logger.info(f"[{pdf_name}] Attempting fallback to non-streaming method...")
                return await self.fallback_download(pdf_id, pdf_name, out_path)
            else:
                raise
                
    async def _wait_for_format_completion(self, pdf_id: str, format_ext: str, max_wait_time: int = 60) -> bool:
        """Wait for a specific format conversion to complete
        
        Args:
            pdf_id: PDF ID
            format_ext: Format extension (md, docx, etc.)
            max_wait_time: Maximum wait time in seconds
            
        Returns:
            bool: True if format completed, False if timed out
        """
        start_time = time.time()
        
        while True:
            try:
                # Check conversion status
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(
                        f"{MathpixClient.BASE_URL}/converter/{pdf_id}",
                        headers=self.client.headers
                    )
                    resp.raise_for_status()
                    
                    status_data = resp.json()
                    if "conversion_status" in status_data:
                        format_status = status_data["conversion_status"].get(format_ext, {}).get("status")
                        if format_status == "completed":
                            logger.info(f"Format {format_ext} completed for {pdf_id}")
                            return True
                        elif format_status == "error":
                            error_info = status_data["conversion_status"][format_ext].get("error_info", {})
                            logger.error(f"Format {format_ext} failed for {pdf_id}: {error_info}")
                            return False
            except Exception as e:
                logger.warning(f"Error checking format status: {e}")
            
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                logger.warning(f"Timeout waiting for {format_ext} format completion after {elapsed:.1f}s")
                return False
            
            # Wait before checking again
            await asyncio.sleep(5)
    
    async def _handle_streaming(self, pdf_id: str, pdf_name: str, out_path: str) -> Tuple[str, int, int]:
        """Handle the streaming part of the conversion"""
        stream_url = f"{MathpixClient.PDF_ENDPOINT}/{pdf_id}/stream"
        logger.info(f"[{pdf_name}] Starting stream from {stream_url}...")
        
        # Create/open the output file
        with open(out_path, "w", encoding="utf8") as outf:
            content = {}  # Using dict for page index to content mapping
            expected_total_pages = 0
            progress_bar = None
            
            try:
                logger.debug(f"[{pdf_name}] Establishing stream connection...")
                
                # Get client and stream
                resp = await self.client.stream_pdf_results(pdf_id, pdf_name)
                
                try:
                    logger.debug(f"HTTP Request: GET {stream_url} \"{resp.status_code} {resp.reason_phrase}\"")
                    resp.raise_for_status()
                    logger.debug(f"[{pdf_name}] Stream connection established")
                    
                    # Process each line of the stream
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                            
                        try:
                            logger.debug(f"[{pdf_name}] Received line: {line[:100]}...")
                            data = json.loads(line)
                            page_idx = data.get("page_idx", 0)
                            text = data.get("text", "")
                            total_pages = data.get("pdf_selected_len", 0)
                            
                            if total_pages > 0 and expected_total_pages != total_pages:
                                expected_total_pages = total_pages
                                # Initialize or update the progress bar
                                if self.show_progress:
                                    if progress_bar:
                                        progress_bar.total = expected_total_pages
                                        progress_bar.refresh()
                                    else:
                                        progress_bar = tqdm(
                                            total=expected_total_pages,
                                            desc=f"Processing {pdf_name}",
                                            unit="page",
                                            position=0,
                                            leave=True
                                        )
                            
                            # Store content by page index
                            content[page_idx] = text
                            
                            # Update progress bar
                            if self.show_progress and progress_bar:
                                progress_bar.n = len(content)
                                progress_bar.set_postfix({"Current page": page_idx})
                                progress_bar.refresh()
                            
                            logger.info(f"[{pdf_name}] Received page {page_idx}/{expected_total_pages}")
                            
                            # Write current progress to file
                            # Sort by page index to ensure correct order
                            sorted_content = [content.get(i, "") for i in range(1, max(content.keys()) + 1)]
                            full_content = "".join(sorted_content)
                            
                            outf.seek(0)
                            outf.truncate()
                            outf.write(full_content)
                            outf.flush()
                            
                            # Check if we have all pages
                            if (expected_total_pages > 0 and 
                                len(content) >= expected_total_pages and
                                all(i in content for i in range(1, expected_total_pages + 1))):
                                logger.info(f"[{pdf_name}] All {expected_total_pages} pages received!")
                                if self.show_progress and progress_bar:
                                    progress_bar.n = expected_total_pages
                                    progress_bar.refresh()
                                break
                            
                        except json.JSONDecodeError:
                            logger.error(f"[{pdf_name}] Failed to decode line: {line}")
                finally:
                    # Make sure we close the client when done
                    await resp._client.aclose()
                            
            except httpx.HTTPStatusError as e:
                logger.error(f"[{pdf_name}] HTTP error during streaming: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.ReadTimeout as e:
                logger.error(f"[{pdf_name}] Timeout during streaming: {e}")
                # If we have content but hit a timeout, we may still have a valid result
                if len(content) > 0:
                    logger.warning(f"[{pdf_name}] Stream timeout, but {len(content)} pages were received")
                else:
                    raise
            except httpx.RemoteProtocolError as e:
                logger.error(f"[{pdf_name}] Remote protocol error during streaming: {e}")
                # If we have content but hit a connection issue, try to use what we have
                if len(content) > 0:
                    logger.warning(f"[{pdf_name}] Stream connection dropped, but {len(content)} pages were received")
                    # Write current progress to file
                    sorted_content = [content.get(i, "") for i in range(1, max(content.keys()) + 1) if i in content]
                    full_content = "".join(sorted_content)
                    
                    outf.seek(0)
                    outf.truncate()
                    outf.write(full_content)
                    outf.flush()
                else:
                    raise
            except Exception as e:
                logger.error(f"[{pdf_name}] Error during streaming: {e}")
                logger.error(traceback.format_exc())
                raise
            finally:
                if self.show_progress and progress_bar:
                    progress_bar.close()
            
            # Final check - did we get all the pages?
            if expected_total_pages > 0 and len(content) < expected_total_pages:
                logger.warning(f"[{pdf_name}] Only received {len(content)}/{expected_total_pages} pages")
            else:
                logger.info(f"[{pdf_name}] Completed and saved → {out_path}")
                # Print minimal success message if not verbose
                if not logger.verbose and self.show_progress:
                    print(f"✅ {pdf_name} → {out_path}")
                
            return pdf_id, len(content), expected_total_pages
    
    async def fallback_download(self, pdf_id: str, pdf_name: str, out_path: str) -> Tuple[str, int, int]:
        """Fallback method to download the MMD file if streaming fails"""
        try:
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            progress_bar = None
            
            # First check status
            status_data = await self.client.get_pdf_status(pdf_id, pdf_name)
            num_pages = status_data.get("num_pages", 0)
            
            if self.show_progress and num_pages > 0:
                progress_bar = tqdm(
                    total=num_pages,
                    desc=f"Processing {pdf_name} (fallback)",
                    unit="page",
                    position=0,
                    leave=True
                )
            
            while True:
                status_data = await self.client.get_pdf_status(pdf_id, pdf_name)
                status = status_data.get("status")
                
                logger.info(f"[{pdf_name}] PDF status: {status}")
                logger.debug(f"[{pdf_name}] Status data: {status_data}")
                
                # Get progress info
                num_pages = status_data.get("num_pages", 0)
                num_pages_completed = status_data.get("num_pages_completed", 0)
                percent_done = status_data.get("percent_done", 0)
                
                # Update progress bar
                if self.show_progress and progress_bar:
                    progress_bar.n = num_pages_completed
                    progress_bar.total = num_pages
                    progress_bar.set_postfix({"Completed": f"{percent_done:.1f}%"})
                    progress_bar.refresh()
                
                if status == "completed":
                    break
                if status == "error":
                    error_msg = status_data.get("error", "Unknown error")
                    raise RuntimeError(f"Conversion failed for {pdf_name}: {error_msg}")
                
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > max_wait_time:
                    logger.warning(f"[{pdf_name}] Timeout waiting for PDF processing after {elapsed:.1f}s")
                    break
                
                logger.info(f"[{pdf_name}] Processing: {percent_done:.1f}% ({num_pages_completed}/{num_pages} pages)")
                await asyncio.sleep(5)
            
            # Download MMD even if status is not "completed" - we might have partial results
            mmd = await self.client.download_mmd(pdf_id, pdf_name)
            if not mmd:
                return pdf_id, 0, 0
                
            # Write file
            with open(out_path, "w", encoding="utf8") as outf:
                outf.write(mmd)
                
            logger.info(f"[{pdf_name}] Fallback method successful, saved → {out_path}")
            # Print minimal success message if not verbose
            if not logger.verbose and self.show_progress:
                print(f"✅ {pdf_name} → {out_path} (fallback method)")
            
            # Make sure progress bar shows 100%
            if self.show_progress and progress_bar:
                progress_bar.n = progress_bar.total
                progress_bar.refresh()
                progress_bar.close()
            
            # Get approximate page count from status data
            return pdf_id, num_pages_completed, num_pages
            
        except Exception as e:
            logger.error(f"[{pdf_name}] Fallback method failed: {e}")
            logger.error(traceback.format_exc())
            if self.show_progress and 'progress_bar' in locals() and progress_bar:
                progress_bar.close()
            raise RuntimeError(f"Failed to convert {pdf_name} using both methods")
            
    async def check_final_status(self, pdf_id: str, pdf_name: str, skip_status_check: bool = False) -> bool:
        """Check the final status of a PDF after streaming/conversion"""
        if skip_status_check:
            logger.info(f"[{pdf_name}] Skipping final status check as requested")
            return True
            
        try:
            status_data = await self.client.get_pdf_status(pdf_id, pdf_name)
            status = status_data.get("status")
            
            if status == "completed":
                logger.info(f"[{pdf_name}] Final status check: PDF processing is complete")
                return True
            elif status == "split" or status == "processing":
                # This is normal with streaming - we have the content before processing fully completes
                logger.info(f"[{pdf_name}] PDF backend processing still in progress (status: {status})")
                logger.info(f"[{pdf_name}] This is normal when using streaming - your output file should be complete")
                return True
            else:
                logger.warning(f"[{pdf_name}] Unexpected status: {status}")
                return False
                    
        except Exception as e:
            logger.error(f"[{pdf_name}] Error checking final status: {e}")
            return False

class BatchProcessor:
    """Handles batch processing of multiple PDFs"""
    
    def __init__(self, client: MathpixClient, options: Dict[str, Any], skip_status_check: bool = False, show_progress: bool = True, download_images: bool = True):
        self.client = client
        self.options = options
        self.skip_status_check = skip_status_check
        self.show_progress = show_progress
        self.download_images = download_images
        self.converter = PDFConverter(client, options, show_progress)
        
    async def count_total_pages(self, pdfs: List[str]) -> int:
        """Count total pages across all PDFs"""
        total_pages = 0
        
        if self.show_progress and len(pdfs) > 1:
            print("Checking PDFs to count pages...")
            page_count_progress = tqdm(
                total=len(pdfs),
                desc="Counting pages",
                unit="PDF",
                position=0,
                leave=True
            )
            
            for pdf in pdfs:
                pdf_name = os.path.basename(pdf)
                try:
                    # Get PDF page count by submitting it first
                    response = await self.client.submit_pdf(pdf, self.options)
                    pdf_id = response["pdf_id"]
                    
                    # Check status to get page count
                    for _ in range(5):  # Try a few times
                        status_data = await self.client.get_pdf_status(pdf_id, pdf_name)
                        num_pages = status_data.get("num_pages", 0)
                        if num_pages > 0:
                            total_pages += num_pages
                            break
                        await asyncio.sleep(1)
                except Exception as e:
                    logger.warning(f"Could not determine page count for {pdf_name}: {e}")
                    # Assume a default of 5 pages if we can't determine
                    total_pages += 5
                
                page_count_progress.update(1)
            
            page_count_progress.close()
            print(f"Found {total_pages} total pages across {len(pdfs)} PDFs")
            
        return total_pages
        
    async def process_all(self, pdfs: List[str], out_dir: str, anonymize_method: str = 'hash') -> List[Dict[str, Any]]:
        """Process a batch of PDFs with a page-based progress bar"""
        results = []
        total_pages = 0
        completed_pages = 0
        
        # First, determine total page count
        if self.show_progress and len(pdfs) > 1:
            total_pages = await self.count_total_pages(pdfs)
        
        # Create overall progress bar for all pages
        batch_progress = None
        if self.show_progress and len(pdfs) > 1 and total_pages > 0:
            batch_progress = tqdm(
                total=total_pages,
                desc="Overall progress",
                unit="page",
                position=0,
                leave=True
            )
        
        try:
            for i, pdf in enumerate(pdfs):
                base = os.path.splitext(os.path.basename(pdf))[0]
                out_file = os.path.join(out_dir, f"{base}.mmd")
                try:
                    if len(pdfs) > 1 and not logger.verbose and self.show_progress:
                        print(f"\nProcessing {i+1}/{len(pdfs)}: {os.path.basename(pdf)}")
                    logger.info(f"Processing PDF {i+1}/{len(pdfs)}: {os.path.basename(pdf)}")
                    
                    result = await self.converter.convert_with_streaming(
                        pdf, 
                        out_file, 
                        anonymize_method, 
                        self.download_images
                    )
                    
                    if isinstance(result, tuple) and len(result) == 3:
                        pdf_id, pages_received, total_pages_in_pdf = result
                        if pages_received > 0 and pages_received >= total_pages_in_pdf:
                            logger.info(f"[{os.path.basename(pdf)}] Successfully received all pages ({pages_received}/{total_pages_in_pdf})")
                        elif pages_received > 0:
                            logger.warning(f"[{os.path.basename(pdf)}] Partial content: received {pages_received}/{total_pages_in_pdf} pages")
                        
                        # Update overall progress by the number of pages we processed
                        completed_pages += pages_received
                        if self.show_progress and batch_progress:
                            # Update to reflect actual pages processed
                            batch_progress.n = completed_pages
                            batch_progress.refresh()
                        
                        # Verify completion with a status check
                        success = await self.converter.check_final_status(
                            pdf_id, 
                            os.path.basename(pdf), 
                            self.skip_status_check
                        )
                        
                        results.append({
                            "pdf": pdf,
                            "out_file": out_file,
                            "pdf_id": pdf_id,
                            "pages_received": pages_received,
                            "total_pages": total_pages_in_pdf,
                            "success": success
                        })
                    else:
                        logger.warning(f"[{os.path.basename(pdf)}] Unexpected result format: {result}")
                        results.append({
                            "pdf": pdf,
                            "out_file": out_file,
                            "success": False,
                            "error": "Unexpected result format"
                        })
                except Exception as e:
                    logger.error(f"Error with {pdf}: {e}")
                    logger.error(traceback.format_exc())
                    results.append({
                        "pdf": pdf,
                        "out_file": out_file,
                        "success": False,
                        "error": str(e)
                    })
        finally:
            if self.show_progress and batch_progress:
                batch_progress.close()
        
        # Summary
        self._print_summary(results)
        
        return results
        
    def _print_summary(self, results: List[Dict[str, Any]]) -> None:
        """Print summary of batch process results"""
        total_pages_processed = sum(r.get("pages_received", 0) for r in results)
        total_pages_expected = sum(r.get("total_pages", 0) for r in results)
        success_count = sum(1 for r in results if r.get("success", False))
        
        if not logger.verbose and self.show_progress and len(results) > 1:
            print(f"\nConversion complete: {success_count}/{len(results)} PDFs converted successfully")
            print(f"Processed {total_pages_processed}/{total_pages_expected} pages")
        
        logger.info(f"Batch processing complete: {success_count}/{len(results)} PDFs converted successfully")
        logger.info(f"Processed {total_pages_processed}/{total_pages_expected} pages")
        
        if len(results) > 1 and not logger.verbose:
            print("\nConversion Summary:")
            for result in results:
                pdf_name = os.path.basename(result["pdf"])
                if result.get("success", False):
                    pages = f"{result.get('pages_received', 0)}/{result.get('total_pages', 0)} pages"
                    print(f"✅ {pdf_name}: {pages}")
                else:
                    error = result.get("error", "Unknown error")
                    print(f"❌ {pdf_name}: {error}")

def parse_args():
    p = argparse.ArgumentParser(
        description="Batch‑convert a folder of PDFs to Mathpix‑Markdown using streaming")
    p.add_argument("input", help="Path to PDF file or directory of PDFs", nargs='?')
    p.add_argument("-o", "--out-dir",
                   help="Directory to write .mmd files (default: same as PDF folder)")
    p.add_argument("-v", "--verbose", action="store_true", 
                   help="Enable verbose logging")
    p.add_argument("--skip-status-check", action="store_true",
                   help="Skip final status check (use when all pages are received via streaming)")
    p.add_argument("--silent", action="store_true",
                   help="Hide progress bars (only show log messages)")
    p.add_argument("--anonymize", choices=["hash", "uuid", "simple", "none"], default="hash",
                   help="Method to anonymize filenames when sending to Mathpix (default: hash)")
    p.add_argument("--check-hash", help="Check what the anonymized filename would be for a given PDF file")
    p.add_argument("--list-documents", action="store_true",
                   help="List all documents previously processed by the Mathpix API")
    p.add_argument("--delete-document", 
                   help="Delete a document from the Mathpix server using its PDF ID")
    p.add_argument("--page", type=int, default=1,
                   help="Page number for listing documents (default: 1)")
    p.add_argument("--per-page", type=int, default=50,
                   help="Number of documents per page (default: 50)")
    p.add_argument("--from-date", 
                   help="Filter documents from this date (format: YYYY-MM-DD)")
    p.add_argument("--to-date", 
                   help="Filter documents to this date (format: YYYY-MM-DD)")
    p.add_argument("--download-document", 
                   help="Download a document from the Mathpix server using its PDF ID")
    p.add_argument("--output-format", 
                   help="Format to download the document (default: mmd)", default="mmd")
    p.add_argument("--output-path", 
                   help="Path to save the downloaded document")
    p.add_argument("--skip-existence-check", action="store_true",
                   help="Skip existence check for documents in list (default: False)")
    p.add_argument("--no-images", action="store_true",
                   help="Don't download images from Mathpix CDN (default: False)")
    p.add_argument("--download-images", action="store_true",
                   help="Force download images for existing MMD files")
    return p.parse_args()

def get_pdf_list(path):
    if os.path.isdir(path):
        return [os.path.join(path, fn)
                for fn in os.listdir(path)
                if fn.lower().endswith(".pdf")]
    elif os.path.isfile(path) and path.lower().endswith(".pdf"):
        return [path]
    else:
        raise ValueError(f"No PDF(s) found at {path!r}")

async def async_main():
    args = parse_args()
    
    # Set logger verbosity
    logger.set_verbose(args.verbose)
    
    # Set logging level based on verbose flag
    if args.verbose:
        logger.set_level(logging.DEBUG)
    
    load_dotenv()
    
    APP_ID = os.getenv("MATHPIX_APP_ID")
    APP_KEY = os.getenv("MATHPIX_APP_KEY")
    
    if not APP_ID or not APP_KEY:
        raise RuntimeError("Set MATHPIX_APP_ID and MATHPIX_APP_KEY in your .env")
    
    # Create Mathpix client
    client = MathpixClient(APP_ID, APP_KEY)
    logger.debug(f"Using app_id: {APP_ID}")
    
    # Handle download images for existing files
    if args.download_images:
        if not args.input:
            print("Error: The 'input' argument is required when using --download-images.")
            print("Specify a .mmd, .md, or .json file, or a directory containing such files.")
            return
            
        # Process file or directory
        if os.path.isfile(args.input):
            file_ext = os.path.splitext(args.input)[1].lower()
            
            if file_ext in ('.mmd', '.md'):
                print(f"Processing images in {args.input}...")
                image_count = process_markdown_images(args.input, True)
                print(f"✅ Downloaded {image_count} images from {args.input}")
                return
            elif file_ext == '.json':
                # Check if it's a lines.mmd.json or lines.json file
                if args.input.endswith('.lines.mmd.json') or args.input.endswith('.lines.json'):
                    print(f"Processing images in {args.input}...")
                    image_count = process_json_images(args.input)
                    print(f"✅ Downloaded {image_count} images from {args.input}")
                    return
                else:
                    print(f"Warning: {args.input} is not a recognized Mathpix JSON format (.lines.json or .lines.mmd.json)")
                    print("Attempting to process anyway...")
                    image_count = process_json_images(args.input)
                    print(f"✅ Downloaded {image_count} images from {args.input}")
                    return
            else:
                print(f"Error: {args.input} is not a supported file format.")
                print("Supported formats are .mmd, .md, .lines.json, and .lines.mmd.json")
                return
        elif os.path.isdir(args.input):
            # Find all markdown and JSON files in directory
            supported_files = []
            for root, _, files in os.walk(args.input):
                for file in files:
                    if file.lower().endswith(('.mmd', '.md')) or file.lower().endswith(('.lines.json', '.lines.mmd.json')):
                        supported_files.append(os.path.join(root, file))
            
            if not supported_files:
                print(f"No supported files found in {args.input}")
                return
                
            print(f"Found {len(supported_files)} files to process")
            
            total_images = 0
            for file_path in supported_files:
                file_ext = os.path.splitext(file_path)[1].lower()
                print(f"Processing images in {os.path.basename(file_path)}...")
                
                if file_ext in ('.mmd', '.md'):
                    image_count = process_markdown_images(file_path, True)
                    total_images += image_count
                    print(f"  → Downloaded {image_count} images")
                elif file_ext == '.json':
                    image_count = process_json_images(file_path)
                    total_images += image_count
                    print(f"  → Downloaded {image_count} images")
                
            print(f"\n✅ Downloaded {total_images} images from {len(supported_files)} files")
            return
        else:
            print(f"Error: {args.input} is not a file or directory")
            return
    
    # you can tweak these options as needed
    options = {
        "math_inline_delimiters": ["$", "$"],
        "rm_spaces": True,
        "include_equation_tags": True,
        "enable_tables_fallback": True,  # Enable advanced table processing algorithm
    }
    
    # Handle list documents option
    if args.list_documents:
        # Convert date format for API if provided
        from_date = None
        if args.from_date:
            from_date = f"{args.from_date}T00:00:00.000Z"
            
        to_date = None
        if args.to_date:
            to_date = f"{args.to_date}T23:59:59.999Z"
            
        print(f"\nRetrieving documents from Mathpix server (page {args.page}, {args.per_page} per page)...")
        
        try:
            documents = await client.list_documents(
                per_page=args.per_page,
                page=args.page,
                from_date=from_date,
                to_date=to_date
            )
            
            if "pdfs" in documents and documents["pdfs"]:
                pdfs = documents["pdfs"]
                
                # Check if the documents still exist
                if not args.skip_existence_check:
                    print(f"Checking document existence status (this might take a moment)...")
                    existence_progress = None
                    
                    # Create progress bar if not in silent mode
                    if not args.silent:
                        existence_progress = tqdm(
                            total=len(pdfs),
                            desc="Checking document existence",
                            unit="doc",
                            position=0,
                            leave=True
                        )
                    
                    for pdf in pdfs:
                        pdf_id = pdf.get("id", "N/A")
                        # Check if the document still exists
                        exists = await client.document_exists(pdf_id)
                        pdf["exists"] = exists
                        
                        if existence_progress:
                            existence_progress.update(1)
                    
                    if existence_progress:
                        existence_progress.close()
                
                print(f"\nFound {len(pdfs)} document(s):\n")
                
                # Display header
                print(f"{'ID':<36} {'File':<30} {'Status':<12} {'Created':<24} {'Pages':<10} {'Exists':<6}")
                print("-" * 120)
                
                # Display each document
                for pdf in pdfs:
                    pdf_id = pdf.get("id", "N/A")
                    filename = os.path.basename(pdf.get("input_file", "Unknown"))
                    status = pdf.get("status", "Unknown")
                    created_at = pdf.get("created_at", "Unknown")
                    pages = f"{pdf.get('num_pages_completed', 0)}/{pdf.get('num_pages', 0)}"
                    
                    # Add existence status if available
                    exists_status = "Yes" if pdf.get("exists", True) else "No"
                    
                    print(f"{pdf_id:<36} {filename:<30} {status:<12} {created_at:<24} {pages:<10} {exists_status:<6}")
                
                print("\nTo download or convert any of these documents, use --download-document with the PDF ID.")
                
                # Show pagination info if relevant
                if len(pdfs) == args.per_page:
                    print(f"\nShowing page {args.page}. For more results, use --page {args.page + 1}")
            else:
                print("No documents found.")
            
            return
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return
    
    # Handle delete document option
    if args.delete_document:
        pdf_id = args.delete_document
        print(f"\nDeleting document with ID: {pdf_id}...")
        
        try:
            response = await client.delete_document(pdf_id)
            if response.get("success"):
                print(f"✅ Document {pdf_id} deleted successfully.")
                print("\nNote: The document may still appear in listings for a short time due to server-side caching.")
                print("If you need to confirm deletion, wait a few minutes and run --list-documents again.")
            else:
                print(f"❌ Failed to delete document {pdf_id}: {response.get('message', 'Unknown error')}")
            return
        except Exception as e:
            print(f"❌ Error deleting document: {e}")
            return
    
    # Handle check hash option
    if args.check_hash:
        file_path = args.check_hash
        if not os.path.isfile(file_path):
            print(f"Error: File not found at {file_path}")
            return
        
        anonymized_name = get_anonymized_filename(file_path, args.anonymize)
        print(f"Anonymized filename for {file_path}: {anonymized_name}")
        return
    
    # Handle download document option
    if args.download_document:
        pdf_id = args.download_document
        output_format = args.output_format
        output_path = args.output_path
        
        print(f"\nDownloading document with ID: {pdf_id} in format: {output_format}...")
        
        try:
            output_path = await client.download_document(pdf_id, output_format, output_path)
            print(f"✅ Document downloaded successfully to {output_path}")
            return
        except Exception as e:
            print(f"❌ Error downloading document: {e}")
            return
    
    # Validate input parameter is provided when not performing specific operations
    if not args.input:
        print("Error: The 'input' argument is required when not using --list-documents, --delete-document, or --download-document.")
        print("Use --help for more information.")
        return
    
    pdfs = get_pdf_list(args.input)
    if not pdfs:
        print("No PDFs found.")
        return
        
    if not args.verbose:
        print(f"Found {len(pdfs)} PDF file(s) to process")
    logger.info(f"Found {len(pdfs)} PDF files to process")
    
    out_dir = args.out_dir or os.path.dirname(os.path.abspath(pdfs[0]))
    os.makedirs(out_dir, exist_ok=True)
    
    # Process batch of PDFs
    batch_processor = BatchProcessor(
        client, 
        options, 
        args.skip_status_check, 
        not args.silent,
        not args.no_images  # Download images by default unless --no-images is specified
    )
    
    await batch_processor.process_all(pdfs, out_dir, args.anonymize)
    
def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
