#!/usr/bin/env python3
import os
import json
import requests
import argparse
import asyncio
import httpx
import traceback
import logging
import time
import sys
from dotenv import load_dotenv
from tqdm import tqdm

# Configure a null handler by default
logging.getLogger().addHandler(logging.NullHandler())

# Custom logger that respects verbose flag
class ConditionalLogger:
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

def parse_args():
    p = argparse.ArgumentParser(
        description="Batch‑convert a folder of PDFs to Mathpix‑Markdown using streaming")
    p.add_argument("input", help="Path to PDF file or directory of PDFs")
    p.add_argument("-o", "--out-dir",
                   help="Directory to write .mmd files (default: same as PDF folder)")
    p.add_argument("-v", "--verbose", action="store_true", 
                   help="Enable verbose logging")
    p.add_argument("--skip-status-check", action="store_true",
                   help="Skip final status check (use when all pages are received via streaming)")
    p.add_argument("--silent", action="store_true",
                   help="Hide progress bars (only show log messages)")
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

async def convert_pdf_streaming(pdf_path, out_path, headers, options, show_progress=True):
    pdf_name = os.path.basename(pdf_path)
    
    # Add streaming option
    options["streaming"] = True
    
    # 1) submit PDF
    logger.info(f"[{pdf_name}] Submitting PDF...")
    pdf_id = None
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            with open(pdf_path, "rb") as f:
                files = {"file": f}
                data = {"options_json": json.dumps(options)}
                
                logger.debug(f"[{pdf_name}] POST request with options: {options}")
                
                resp = await client.post(
                    "https://api.mathpix.com/v3/pdf",
                    headers=headers,
                    files=files,
                    data=data
                )
            
            logger.debug(f"HTTP Request: POST https://api.mathpix.com/v3/pdf \"{resp.status_code} {resp.reason_phrase}\"")
            resp.raise_for_status()
            response_json = resp.json()
            logger.debug(f"[{pdf_name}] Submit response: {response_json}")
            
            pdf_id = response_json["pdf_id"]
            logger.info(f"[{pdf_name}] submitted → pdf_id={pdf_id}")
            
            # 2) Stream results and write to file incrementally
            stream_url = f"https://api.mathpix.com/v3/pdf/{pdf_id}/stream"
            logger.info(f"[{pdf_name}] Starting stream from {stream_url}...")
            
            # Create/open the output file
            with open(out_path, "w", encoding="utf8") as outf:
                content = {}  # Using dict for page index to content mapping
                expected_total_pages = 0
                progress_bar = None
                
                try:
                    logger.debug(f"[{pdf_name}] Establishing stream connection...")
                    
                    # Using a longer timeout for stream connection
                    async with client.stream("GET", stream_url, headers=headers, timeout=300.0) as stream:
                        logger.debug(f"HTTP Request: GET {stream_url} \"{stream.status_code} {stream.reason_phrase}\"")
                        stream.raise_for_status()
                        logger.debug(f"[{pdf_name}] Stream connection established")
                        
                        # Process each line of the stream
                        async for line in stream.aiter_lines():
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
                                    if show_progress:
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
                                if show_progress and progress_bar:
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
                                    if show_progress and progress_bar:
                                        progress_bar.n = expected_total_pages
                                        progress_bar.refresh()
                                    break
                                
                            except json.JSONDecodeError:
                                logger.error(f"[{pdf_name}] Failed to decode line: {line}")
                                
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
                except Exception as e:
                    logger.error(f"[{pdf_name}] Error during streaming: {e}")
                    logger.error(traceback.format_exc())
                    raise
                finally:
                    if show_progress and progress_bar:
                        progress_bar.close()
                
                # Final check - did we get all the pages?
                if expected_total_pages > 0 and len(content) < expected_total_pages:
                    logger.warning(f"[{pdf_name}] Only received {len(content)}/{expected_total_pages} pages")
                else:
                    logger.info(f"[{pdf_name}] Completed and saved → {out_path}")
                    # Print minimal success message if not verbose
                    if not logger.verbose and show_progress:
                        print(f"✅ {pdf_name} → {out_path}")
                    
                return pdf_id, len(content), expected_total_pages
                    
    except Exception as e:
        logger.error(f"[{pdf_name}] Conversion failed: {e}")
        logger.error(traceback.format_exc())
        
        # If we have a pdf_id but streaming failed, we can fall back to non-streaming method
        if pdf_id:
            logger.info(f"[{pdf_name}] Attempting fallback to non-streaming method...")
            return await fallback_pdf_download(pdf_id, pdf_name, out_path, headers, show_progress)
        else:
            raise

async def fallback_pdf_download(pdf_id, pdf_name, out_path, headers, show_progress=True):
    """Fallback method to download the MMD file if streaming fails"""
    try:
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        progress_bar = None
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # First check status
            status_url = f"https://api.mathpix.com/v3/pdf/{pdf_id}"
            logger.info(f"[{pdf_name}] Checking PDF status at {status_url}")
            
            # Get initial status to setup progress bar
            r = await client.get(status_url, headers=headers)
            r.raise_for_status()
            status_data = r.json()
            num_pages = status_data.get("num_pages", 0)
            
            if show_progress and num_pages > 0:
                progress_bar = tqdm(
                    total=num_pages,
                    desc=f"Processing {pdf_name} (fallback)",
                    unit="page",
                    position=0,
                    leave=True
                )
            
            while True:
                r = await client.get(status_url, headers=headers)
                logger.debug(f"HTTP Request: GET {status_url} \"{r.status_code} {r.reason_phrase}\"")
                r.raise_for_status()
                status_data = r.json()
                status = status_data.get("status")
                
                logger.info(f"[{pdf_name}] PDF status: {status}")
                logger.debug(f"[{pdf_name}] Status data: {status_data}")
                
                # Get progress info
                num_pages = status_data.get("num_pages", 0)
                num_pages_completed = status_data.get("num_pages_completed", 0)
                percent_done = status_data.get("percent_done", 0)
                
                # Update progress bar
                if show_progress and progress_bar:
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
            mmd_url = f"https://api.mathpix.com/v3/pdf/{pdf_id}.mmd"
            logger.info(f"[{pdf_name}] Downloading MMD from {mmd_url}")
            
            r = await client.get(mmd_url, headers=headers)
            logger.debug(f"HTTP Request: GET {mmd_url} \"{r.status_code} {r.reason_phrase}\"")
            
            if r.status_code == 404:
                logger.error(f"[{pdf_name}] MMD file not available yet (404)")
                return pdf_id, 0, 0
                
            r.raise_for_status()
            mmd = r.text
            
            # Write file
            with open(out_path, "w", encoding="utf8") as outf:
                outf.write(mmd)
                
            logger.info(f"[{pdf_name}] Fallback method successful, saved → {out_path}")
            # Print minimal success message if not verbose
            if not logger.verbose and show_progress:
                print(f"✅ {pdf_name} → {out_path} (fallback method)")
            
            # Make sure progress bar shows 100%
            if show_progress and progress_bar:
                progress_bar.n = progress_bar.total
                progress_bar.refresh()
                progress_bar.close()
            
            # Get approximate page count from status data
            return pdf_id, num_pages_completed, num_pages
            
    except Exception as e:
        logger.error(f"[{pdf_name}] Fallback method failed: {e}")
        logger.error(traceback.format_exc())
        if show_progress and progress_bar:
            progress_bar.close()
        raise RuntimeError(f"Failed to convert {pdf_name} using both methods")

async def check_pdf_status(pdf_id, pdf_name, headers, skip_status_check=False):
    """Check the final status of a PDF after streaming/conversion"""
    if skip_status_check:
        logger.info(f"[{pdf_name}] Skipping final status check as requested")
        return True
        
    try:
        status_url = f"https://api.mathpix.com/v3/pdf/{pdf_id}"
        async with httpx.AsyncClient() as client:
            r = await client.get(status_url, headers=headers)
            logger.debug(f"HTTP Request: GET {status_url} \"{r.status_code} {r.reason_phrase}\"")
            r.raise_for_status()
            status_data = r.json()
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

async def process_batch(pdfs, out_dir, headers, options, skip_status_check=False, show_progress=True):
    """Process a batch of PDFs with a batch progress bar"""
    results = []
    
    # Create overall progress bar for all PDFs
    if show_progress and len(pdfs) > 1:
        batch_progress = tqdm(
            total=len(pdfs),
            desc="Overall progress",
            unit="PDF",
            position=0,
            leave=True
        )
    else:
        batch_progress = None
    
    try:
        for i, pdf in enumerate(pdfs):
            base = os.path.splitext(os.path.basename(pdf))[0]
            out_file = os.path.join(out_dir, f"{base}.mmd")
            
            try:
                if len(pdfs) > 1 and not logger.verbose and show_progress:
                    print(f"\nProcessing {i+1}/{len(pdfs)}: {os.path.basename(pdf)}")
                logger.info(f"Processing PDF {i+1}/{len(pdfs)}: {os.path.basename(pdf)}")
                
                result = await convert_pdf_streaming(
                    pdf, 
                    out_file, 
                    headers, 
                    options, 
                    show_progress
                )
                
                if isinstance(result, tuple) and len(result) == 3:
                    pdf_id, pages_received, total_pages = result
                    
                    if pages_received > 0 and pages_received >= total_pages:
                        logger.info(f"[{os.path.basename(pdf)}] Successfully received all pages ({pages_received}/{total_pages})")
                    elif pages_received > 0:
                        logger.warning(f"[{os.path.basename(pdf)}] Partial content: received {pages_received}/{total_pages} pages")
                    
                    # Verify completion with a status check
                    success = await check_pdf_status(pdf_id, os.path.basename(pdf), headers, skip_status_check)
                    results.append({
                        "pdf": pdf,
                        "out_file": out_file,
                        "pdf_id": pdf_id,
                        "pages_received": pages_received,
                        "total_pages": total_pages,
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
            
            # Update batch progress
            if show_progress and batch_progress:
                batch_progress.update(1)
                
    finally:
        if show_progress and batch_progress:
            batch_progress.close()
    
    # Summary
    success_count = sum(1 for r in results if r.get("success", False))
    
    if not logger.verbose and show_progress and len(pdfs) > 1:
        print(f"\nConversion complete: {success_count}/{len(pdfs)} PDFs converted successfully")
    
    logger.info(f"Batch processing complete: {success_count}/{len(pdfs)} PDFs converted successfully")
    
    return results

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
    
    headers = {"app_id": APP_ID, "app_key": APP_KEY}
    logger.debug(f"Using app_id: {APP_ID}")
    
    # you can tweak these options as needed
    options = {
        "math_inline_delimiters": ["$", "$"],
        "rm_spaces": True
    }
    
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
    results = await process_batch(
        pdfs, 
        out_dir, 
        headers, 
        options, 
        args.skip_status_check, 
        not args.silent
    )
    
    # Print summary
    if len(results) > 1 and not args.verbose:
        print("\nConversion Summary:")
        for result in results:
            pdf_name = os.path.basename(result["pdf"])
            if result.get("success", False):
                pages = f"{result.get('pages_received', 0)}/{result.get('total_pages', 0)} pages"
                print(f"✅ {pdf_name}: {pages}")
            else:
                error = result.get("error", "Unknown error")
                print(f"❌ {pdf_name}: {error}")

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
