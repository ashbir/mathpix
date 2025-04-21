#!/usr/bin/env python3
import os
import time
import json
import requests
import argparse
from dotenv import load_dotenv

def parse_args():
    p = argparse.ArgumentParser(
        description="Batch‑convert a folder of PDFs to Mathpix‑Markdown")
    p.add_argument("input", help="Path to PDF file or directory of PDFs")
    p.add_argument("-o", "--out-dir",
                   help="Directory to write .mmd files (default: same as PDF folder)")
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

def convert_pdf(pdf_path, out_path, headers, options):
    # 1) submit PDF
    with open(pdf_path, "rb") as f:
        resp = requests.post(
            "https://api.mathpix.com/v3/pdf",
            headers=headers,
            files={"file": f},
            data={"options_json": json.dumps(options)}
        )
    resp.raise_for_status()
    pdf_id = resp.json()["pdf_id"]
    print(f"[{os.path.basename(pdf_path)}] submitted → pdf_id={pdf_id}")

    # 2) poll status
    status_url = f"https://api.mathpix.com/v3/pdf/{pdf_id}"
    while True:
        r = requests.get(status_url, headers=headers)
        r.raise_for_status()
        status = r.json().get("status")
        if status == "completed":
            break
        if status == "error":
            raise RuntimeError(f"Conversion failed for {pdf_path}")
        time.sleep(1)

    # 3) download .mmd
    mmd = requests.get(f"https://api.mathpix.com/v3/pdf/{pdf_id}.mmd",
                       headers=headers).text

    # 4) write file
    with open(out_path, "w", encoding="utf8") as outf:
        outf.write(mmd)
    print(f"[{os.path.basename(pdf_path)}] saved → {out_path}")

def main():
    args = parse_args()
    load_dotenv()

    APP_ID  = os.getenv("MATHPIX_APP_ID")
    APP_KEY = os.getenv("MATHPIX_APP_KEY")
    if not APP_ID or not APP_KEY:
        raise RuntimeError("Set MATHPIX_APP_ID and MATHPIX_APP_KEY in your .env")

    headers = {"app_id": APP_ID, "app_key": APP_KEY}
    # you can tweak these options as needed
    options = {
        "math_inline_delimiters": ["$", "$"],
        "rm_spaces": True
    }

    pdfs = get_pdf_list(args.input)
    if not pdfs:
        print("No PDFs found.")
        return

    out_dir = args.out_dir or os.path.dirname(os.path.abspath(pdfs[0]))
    os.makedirs(out_dir, exist_ok=True)

    for pdf in pdfs:
        base = os.path.splitext(os.path.basename(pdf))[0]
        out_file = os.path.join(out_dir, f"{base}.mmd")
        try:
            convert_pdf(pdf, out_file, headers, options)
        except Exception as e:
            print(f"Error with {pdf}: {e}")

if __name__ == "__main__":
    main()
