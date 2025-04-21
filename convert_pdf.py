import os
import time
import json
import requests
import argparse
from dotenv import load_dotenv

def parse_args():
    p = argparse.ArgumentParser(
        description="Convert a PDF to Mathpix‑Markdown (.mmd)")
    p.add_argument("pdf",
                   help="Path to input PDF file")
    p.add_argument("-o", "--out",
                   help="Path to output .mmd file (default: <pdf_id>.mmd)")
    return p.parse_args()

def main():
    # 0. load credentials
    load_dotenv()
    APP_ID  = os.getenv("MATHPIX_APP_ID")
    APP_KEY = os.getenv("MATHPIX_APP_KEY")
    if not APP_ID or not APP_KEY:
        raise RuntimeError("Missing MATHPIX_APP_ID or MATHPIX_APP_KEY in environment")

    # 1. parse args
    args = parse_args()
    pdf_path = args.pdf

    # 2. submit PDF for OCR
    options = {
        "math_inline_delimiters": ["$", "$"],
        "rm_spaces": True
    }
    headers = {"app_id": APP_ID, "app_key": APP_KEY}
    with open(pdf_path, "rb") as f:
        files = {"file": f}
        data  = {"options_json": json.dumps(options)}
        resp  = requests.post("https://api.mathpix.com/v3/pdf",
                              headers=headers,
                              files=files,
                              data=data)
    resp.raise_for_status()
    pdf_id = resp.json()["pdf_id"]
    print(f"Submitted {pdf_path!r}, got pdf_id = {pdf_id}")

    # 3. poll status
    status_url = f"https://api.mathpix.com/v3/pdf/{pdf_id}"
    while True:
        r = requests.get(status_url, headers=headers)
        r.raise_for_status()
        status = r.json().get("status")
        print("Status:", status)
        if status == "completed":
            break
        if status == "error":
            raise RuntimeError("PDF processing failed")
        time.sleep(1)

    # 4. download .mmd
    mmd_url = f"https://api.mathpix.com/v3/pdf/{pdf_id}.mmd"
    r = requests.get(mmd_url, headers=headers)
    r.raise_for_status()
    markdown = r.text

    # 5. write output
    out_file = args.out or f"{pdf_id}.mmd"
    with open(out_file, "w", encoding="utf8") as f:
        f.write(markdown)
    print(f"Saved Mathpix‑Markdown to {out_file}")

if __name__ == "__main__":
    main()
