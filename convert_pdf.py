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
from dotenv import load_dotenv
from tqdm import tqdm
from typing import Dict, List, Tuple, Optional, Any, Union

# Configure a null handler by default
logging.getLogger().addHandler(logging.NullHandler())

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
        
    async def submit_pdf(self, pdf_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a PDF file to the Mathpix API and return the response"""
        pdf_name = os.path.basename(pdf_path)
        logger.info(f"[{pdf_name}] Submitting PDF...")
        logger.debug(f"[{pdf_name}] POST request with options: {options}")
        
        async with httpx.AsyncClient(timeout=self.default_timeout) as client:
            with open(pdf_path, "rb") as f:
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

class PDFConverter:
    """Handles the conversion of PDFs to Mathpix Markdown"""
    
    def __init__(self, client: MathpixClient, options: Dict[str, Any] = None, show_progress: bool = True):
        self.client = client
        self.options = options or {}
        self.show_progress = show_progress
        
    async def convert_with_streaming(self, pdf_path: str, out_path: str) -> Tuple[str, int, int]:
        """
        Convert a PDF to MMD using streaming API
        
        Returns:
            Tuple[str, int, int]: (pdf_id, pages_received, total_pages)
        """
        pdf_name = os.path.basename(pdf_path)
        
        # Add streaming option
        options = {**self.options, "streaming": True}
        
        try:
            # 1. Submit PDF
            response = await self.client.submit_pdf(pdf_path, options)
            pdf_id = response["pdf_id"]
            logger.info(f"[{pdf_name}] submitted → pdf_id={pdf_id}")
            
            # 2. Stream results and write to file incrementally
            return await self._handle_streaming(pdf_id, pdf_name, out_path)
                    
        except Exception as e:
            logger.error(f"[{pdf_name}] Conversion failed: {e}")
            logger.error(traceback.format_exc())
            
            # If we have a pdf_id but streaming failed, we can fall back
            if 'pdf_id' in locals():
                logger.info(f"[{pdf_name}] Attempting fallback to non-streaming method...")
                return await self.fallback_download(pdf_id, pdf_name, out_path)
            else:
                raise
    
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
    
    def __init__(self, client: MathpixClient, options: Dict[str, Any], skip_status_check: bool = False, show_progress: bool = True):
        self.client = client
        self.options = options
        self.skip_status_check = skip_status_check
        self.show_progress = show_progress
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
        
    async def process_all(self, pdfs: List[str], out_dir: str) -> List[Dict[str, Any]]:
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
                    
                    result = await self.converter.convert_with_streaming(pdf, out_file)
                    
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
    p.add_argument("--list-documents", action="store_true",
                   help="List all documents previously processed by the Mathpix API")
    p.add_argument("--page", type=int, default=1,
                   help="Page number for listing documents (default: 1)")
    p.add_argument("--per-page", type=int, default=50,
                   help="Number of documents per page (default: 50)")
    p.add_argument("--from-date", 
                   help="Filter documents from this date (format: YYYY-MM-DD)")
    p.add_argument("--to-date", 
                   help="Filter documents to this date (format: YYYY-MM-DD)")
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
    
    # you can tweak these options as needed
    options = {
        "math_inline_delimiters": ["$", "$"],
        "rm_spaces": True,
        "include_equation_tags": True,
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
                print(f"\nFound {len(pdfs)} document(s):\n")
                
                # Display header
                print(f"{'ID':<36} {'File':<30} {'Status':<12} {'Created':<24} {'Pages':<10}")
                print("-" * 110)
                
                # Display each document
                for pdf in pdfs:
                    pdf_id = pdf.get("id", "N/A")
                    filename = os.path.basename(pdf.get("input_file", "Unknown"))
                    status = pdf.get("status", "Unknown")
                    created_at = pdf.get("created_at", "Unknown")
                    pages = f"{pdf.get('num_pages_completed', 0)}/{pdf.get('num_pages', 0)}"
                    
                    print(f"{pdf_id:<36} {filename:<30} {status:<12} {created_at:<24} {pages:<10}")
                
                print("\nTo download or convert any of these documents, use the PDF ID with the Mathpix API directly.")
                
                # Show pagination info if relevant
                if len(pdfs) == args.per_page:
                    print(f"\nShowing page {args.page}. For more results, use --page {args.page + 1}")
            else:
                print("No documents found.")
            
            return
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return
    
    # Validate input parameter is provided when not listing documents
    if not args.input:
        print("Error: The 'input' argument is required when not using --list-documents.")
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
        not args.silent
    )
    
    await batch_processor.process_all(pdfs, out_dir)
    
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
