#!/usr/bin/env python3
"""
Script to download images from Mathpix CDN links in markdown files and replace them with local paths.
This script also supports retrieving embedded images from other formats like DOCX, HTML, TEX, and JSON files.

Usage:
    python download_mathpix_images.py [path_to_file.md|mmd|docx|html|json] [--extract-only]
    
If no file is specified, it will process all supported files found in the current directory and subdirectories.
The --extract-only flag will download images but not update references in the original file.
"""

import re
import os
import sys
import json
import zipfile
import requests
import logging
import argparse
import tempfile
import shutil
from urllib.parse import urlparse, unquote
from pathlib import Path
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S"
)

def download_image(url, output_dir):
    """
    Download an image from a URL and save it to the output directory.
    Returns the local path to the saved image.
    """
    try:
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
        else:
            new_filename = filename

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the image to the output directory
        image_path = os.path.join(output_dir, new_filename)
        with open(image_path, 'wb') as f:
            f.write(response.content)
        
        logging.info(f"Downloaded: {url} -> {image_path}")
        return image_path
        
    except Exception as e:
        logging.error(f"Failed to download {url}: {e}")
        return None

def process_markdown_file(file_path, extract_only=False):
    """
    Process a markdown file to download images and update image references.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get the filename without extension to use as the image directory name
        file_basename = os.path.basename(file_path)
        file_name_without_ext = os.path.splitext(file_basename)[0]
        
        # Create directory with the same name as the markdown file
        output_dir = os.path.join(os.path.dirname(file_path), file_name_without_ext)
        
        # Regular expression to find image links
        image_pattern = r'!\[(.*?)\]\((https?://cdn\.mathpix\.com/cropped/.*?)\)'
        
        # Count replacements
        replacement_count = 0
        downloaded_images = []
        
        def replace_image_link(match):
            nonlocal replacement_count
            alt_text = match.group(1)
            image_url = match.group(2)
            
            # Download the image
            local_image_path = download_image(image_url, output_dir)
            
            if local_image_path:
                downloaded_images.append(local_image_path)
                # Get relative path from markdown file to image
                rel_path = os.path.relpath(local_image_path, os.path.dirname(file_path))
                replacement_count += 1
                return f'![{alt_text}]({rel_path})' if not extract_only else match.group(0)
            else:
                # If download failed, keep the original link
                return match.group(0)
        
        # Replace image links in content
        updated_content = re.sub(image_pattern, replace_image_link, content)
        
        # Save updated content back to the file if not extract-only mode
        if not extract_only and updated_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            logging.info(f"Updated {replacement_count} image links in {file_path}")
        else:
            logging.info(f"Downloaded {len(downloaded_images)} images for {file_path}")
        
        return downloaded_images
        
    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
        return []

def process_html_file(file_path, extract_only=False):
    """
    Process an HTML file to download images and update image references.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Get the filename without extension to use as the image directory name
        file_basename = os.path.basename(file_path)
        file_name_without_ext = os.path.splitext(file_basename)[0]
        
        # Create directory with the same name as the HTML file
        output_dir = os.path.join(os.path.dirname(file_path), file_name_without_ext)
        
        # Find all img tags with Mathpix CDN links
        img_tags = soup.find_all('img', src=lambda x: x and 'cdn.mathpix.com' in x)
        
        downloaded_images = []
        replacement_count = 0
        
        for img in img_tags:
            image_url = img['src']
            local_image_path = download_image(image_url, output_dir)
            
            if local_image_path:
                downloaded_images.append(local_image_path)
                if not extract_only:
                    # Update src attribute to use local path
                    rel_path = os.path.relpath(local_image_path, os.path.dirname(file_path))
                    img['src'] = rel_path
                    replacement_count += 1
        
        if not extract_only and replacement_count > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            
            logging.info(f"Updated {replacement_count} image references in {file_path}")
        else:
            logging.info(f"Downloaded {len(downloaded_images)} images for {file_path}")
        
        return downloaded_images
        
    except Exception as e:
        logging.error(f"Error processing HTML file {file_path}: {e}")
        return []

def process_docx_file(file_path, extract_only=True):
    """
    Process a DOCX file to extract and download images.
    Note: DOCX manipulation would require additional libraries like python-docx,
    and the embedded images might not be referenced via URLs. This function
    currently just extracts images without modifying the DOCX.
    """
    try:
        # Get the filename without extension to use as the image directory name
        file_basename = os.path.basename(file_path)
        file_name_without_ext = os.path.splitext(file_basename)[0]
        
        # Create directory with the same name as the DOCX file
        output_dir = os.path.join(os.path.dirname(file_path), file_name_without_ext)
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a temp directory for extraction
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Extract the docx (which is a zip file)
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdirname)
            
            # Look for media files in word/media/
            media_dir = os.path.join(tmpdirname, 'word', 'media')
            downloaded_images = []
            
            if os.path.exists(media_dir):
                for media_file in os.listdir(media_dir):
                    src_path = os.path.join(media_dir, media_file)
                    dest_path = os.path.join(output_dir, media_file)
                    
                    # Copy the image file
                    shutil.copy2(src_path, dest_path)
                    downloaded_images.append(dest_path)
                    logging.info(f"Extracted: {media_file} -> {dest_path}")
            
            # Additionally, look for references to Mathpix CDN in the document.xml
            document_xml = os.path.join(tmpdirname, 'word', 'document.xml')
            if os.path.exists(document_xml):
                tree = ET.parse(document_xml)
                root = tree.getroot()
                
                # XML namespaces in the DOCX
                namespaces = {
                    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
                    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
                    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
                }
                
                # Look for external image references (might contain Mathpix URLs)
                for elem in root.findall('.//w:drawing//a:blip', namespaces):
                    if 'r:embed' in elem.attrib:
                        # This is typically for embedded images
                        pass
                    elif 'r:link' in elem.attrib:
                        # This might be an external link
                        link_id = elem.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}link']
                        # We would need to check the document.xml.rels file to find the URL
            
        logging.info(f"Extracted {len(downloaded_images)} images from {file_path}")
        return downloaded_images
        
    except Exception as e:
        logging.error(f"Error processing DOCX file {file_path}: {e}")
        return []

def process_tex_zip(file_path, extract_only=True):
    """
    Process a TEX.ZIP file to extract and download images.
    """
    try:
        # Get the filename without extension to use as the image directory name
        file_basename = os.path.basename(file_path)
        file_name_without_ext = os.path.splitext(file_basename)[0]
        if file_name_without_ext.endswith('.tex'):
            file_name_without_ext = os.path.splitext(file_name_without_ext)[0]
        
        # Create directory with the same name as the TEX.ZIP file
        output_dir = os.path.join(os.path.dirname(file_path), file_name_without_ext)
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract the zip file
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        
        # The images are extracted to the images folder in the output directory
        images_dir = os.path.join(output_dir, 'images')
        downloaded_images = []
        
        if os.path.exists(images_dir):
            for root, _, files in os.walk(images_dir):
                for image_file in files:
                    image_path = os.path.join(root, image_file)
                    downloaded_images.append(image_path)
        
        logging.info(f"Extracted {len(downloaded_images)} images from {file_path}")
        return downloaded_images
        
    except Exception as e:
        logging.error(f"Error processing TEX.ZIP file {file_path}: {e}")
        return []

def process_json_file(file_path, extract_only=True):
    """
    Process a JSON file to extract and download images from Mathpix CDN URLs.
    This handles both lines.json and lines.mmd.json formats from Mathpix.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        # Get the filename without extension to use as the image directory name
        file_basename = os.path.basename(file_path)
        file_name_without_ext = os.path.splitext(file_basename)[0]
        
        # Create directory with the same name as the JSON file
        output_dir = os.path.join(os.path.dirname(file_path), file_name_without_ext)
        
        # Regular expression to find image links in text content
        image_pattern = r'https?://cdn\.mathpix\.com/cropped/[^)"\'\\s]+'
        
        # Will hold all downloaded image paths
        downloaded_images = []
        
        # Process lines.mmd.json format - has pages with lines that contain text fields
        if 'pages' in content and isinstance(content['pages'], list):
            for page in content['pages']:
                if 'lines' in page and isinstance(page['lines'], list):
                    for line in page['lines']:
                        if 'text' in line and isinstance(line['text'], str):
                            # Extract all Mathpix CDN URLs from the text
                            urls = re.findall(image_pattern, line['text'])
                            for url in urls:
                                # Clean up URL if it contains escape characters or quotes
                                cleaned_url = url.strip('"\\\'"')
                                local_image_path = download_image(cleaned_url, output_dir)
                                if local_image_path:
                                    downloaded_images.append(local_image_path)
                                    
                                    # In non-extract-only mode, we would update the JSON
                                    # This is complex for JSON, so for now we just download
                                    # without modifying the source JSON
        
        # Look for image URLs directly in JSON fields (recursive search)
        def search_json_for_urls(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str):
                        urls = re.findall(image_pattern, value)
                        for url in urls:
                            cleaned_url = url.strip('"\\\'"')
                            local_image_path = download_image(cleaned_url, output_dir)
                            if local_image_path:
                                downloaded_images.append(local_image_path)
                    else:
                        search_json_for_urls(value)
            elif isinstance(obj, list):
                for item in obj:
                    search_json_for_urls(item)
        
        # Recursively search for URLs in the JSON
        search_json_for_urls(content)
        
        logging.info(f"Extracted {len(downloaded_images)} images from {file_path}")
        return downloaded_images
        
    except Exception as e:
        logging.error(f"Error processing JSON file {file_path}: {e}")
        return []

def process_file(file_path, extract_only=False):
    """
    Process a file based on its extension.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in ['.md', '.mmd']:
        return process_markdown_file(file_path, extract_only)
    elif ext == '.html':
        return process_html_file(file_path, extract_only)
    elif ext == '.docx':
        return process_docx_file(file_path, extract_only)
    elif ext == '.zip' and '.tex' in file_path:
        return process_tex_zip(file_path, extract_only)
    elif ext == '.json':
        return process_json_file(file_path, extract_only)
    else:
        logging.warning(f"Unsupported file type: {ext} for file {file_path}")
        return []

def main():
    parser = argparse.ArgumentParser(description='Download and process images from Mathpix-generated files')
    parser.add_argument('input', nargs='?', help='Path to a file or directory to process')
    parser.add_argument('--extract-only', action='store_true', 
                        help='Extract images without modifying the original files')
    parser.add_argument('--formats', nargs='+', default=['md', 'mmd', 'html', 'docx', 'tex.zip', 'json'],
                        help='File formats to process (default: md mmd html docx tex.zip json)')
    args = parser.parse_args()
    
    target_path = args.input or os.getcwd()
    formats = args.formats
    
    # Create file extension patterns from formats
    ext_patterns = []
    for fmt in formats:
        if fmt == 'tex.zip':
            ext_patterns.append(('.zip', lambda f: '.tex.zip' in f or '.tex.zip' in f.lower()))
        else:
            ext_patterns.append((f'.{fmt}', lambda f: True))
    
    if os.path.isdir(target_path):
        # Process all supported files in directory
        total_images = 0
        for root, _, files in os.walk(target_path):
            for file in files:
                file_path = os.path.join(root, file)
                for ext, condition in ext_patterns:
                    if file.endswith(ext) and condition(file_path):
                        images = process_file(file_path, args.extract_only)
                        total_images += len(images)
                        break
        logging.info(f"Total images processed: {total_images}")
    else:
        # Process single file
        images = process_file(target_path, args.extract_only)
        logging.info(f"Total images processed: {len(images)}")

if __name__ == "__main__":
    main()