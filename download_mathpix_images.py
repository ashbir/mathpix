#!/usr/bin/env python3
"""
Script to download images from Mathpix CDN links in markdown files and replace them with local paths.

Usage:
    python download_mathpix_images.py [path_to_file.md]
    
If no file is specified, it will process all markdown files found in the current directory and subdirectories.
"""

import re
import os
import sys
import requests
import logging
from urllib.parse import urlparse, unquote
from pathlib import Path

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

def process_markdown_file(file_path):
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
        
        def replace_image_link(match):
            nonlocal replacement_count
            alt_text = match.group(1)
            image_url = match.group(2)
            
            # Download the image
            local_image_path = download_image(image_url, output_dir)
            
            if local_image_path:
                # Get relative path from markdown file to image
                rel_path = os.path.relpath(local_image_path, os.path.dirname(file_path))
                replacement_count += 1
                return f'![{alt_text}]({rel_path})'
            else:
                # If download failed, keep the original link
                return match.group(0)
        
        # Replace image links in content
        updated_content = re.sub(image_pattern, replace_image_link, content)
        
        # Save updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        logging.info(f"Updated {replacement_count} image links in {file_path}")
        
    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python download_mathpix_images.py <markdown_file_or_directory>")
        sys.exit(1)
        
    target_path = sys.argv[1]
    
    if os.path.isdir(target_path):
        # Process all markdown files in directory
        for root, _, files in os.walk(target_path):
            for file in files:
                if file.endswith('.md') or file.endswith('.mmd'):
                    file_path = os.path.join(root, file)
                    process_markdown_file(file_path)
    else:
        # Process single file
        process_markdown_file(target_path)
        
    logging.info("Processing complete")

if __name__ == "__main__":
    main()