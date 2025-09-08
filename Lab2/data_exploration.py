import argparse
import os
import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

import yfinance as yf
import pdfplumber
import pytesseract
from PIL import Image

# Utils

def ensure_outdir(path: str = "outputs") -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def print_head(df: pd.DataFrame, n: int = 5, title: str = "") -> None:
    print(f"\n=== {title}: first {n} rows ===")
    try:
        print(df.head(n).to_string(index=False))
    except Exception:
        print(df.head(n))
    
def summarize_df(df: pd.DataFrame, name: str = "DataFrame") -> None:
    print(f"\n--- Summary: {name} ---")
    print("Shape:", df.shape)
    print("Columns:", list(df.columns))
    miss = df.isna().sum()
    if miss.sum() == 0:
        print("Missing values: none")
    else:
        print("Missing values by column:")
        print(miss[miss > 0].to_string())
    num = df.select_dtypes(include="number")
    if not num.empty:
        print("\nNumeric describe():")
        print(num.describe().to_string())
        
# (i) CSV/Excel — Finance prices via yfinance

def run_csv_part(ticker: str, period: str, interval: str, outdir: Path) -> None:
    print(f"\n[CSV] Downloading {ticker} ({period}, {interval}) via yfinance …")
    df = yf.download(ticker, period=period, interval=interval, auto_adjust=False, progress=False)
    if df is None or df.empty:
        print(f"[CSV] No data returned for ticker {ticker}.")
        return
    df = df.reset_index()
    csv_path = outdir / f"{ticker}_history.csv"
    df.to_csv(csv_path, index=False)
    print_head(df, title=f"{ticker} CSV")
    summarize_df(df, name=f"{ticker} CSV")
    print("[CSV] Saved:", csv_path)


# (ii) ASCII/HTML — simple text scraping

def extract_visible_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    if len(paras) < 3:  # fallback if page uses other tags
        text = soup.get_text(" ", strip=True)
        return text
    return "\n\n".join(paras)

def run_html_part(url: str, outdir: Path) -> None:
    print(f"\n[HTML] Fetching: {url}")
    headers = {"User-Agent": "Mozilla/5.0 (compatible; DSCI560-Lab2/1.0)"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    text = extract_visible_text_from_html(r.text)
    # Clean whitespace and keep a short excerpt
    text = re.sub(r"\s+", " ", text).strip()
    excerpt = text[:4000]  # keep it short for lab
    txt_path = outdir / "html_text_excerpt.txt"
    txt_path.write_text(excerpt, encoding="utf-8")
    print("[HTML] Saved excerpt to:", txt_path)

    # Make a tiny sentence CSV for “basic operations” demo
    sentences = [s.strip() for s in re.split(r"[.?!]\s+", excerpt) if s.strip()]
    df = pd.DataFrame({"sentence": sentences[:80]})
    csv_path = outdir / "html_sentences_sample.csv"
    df.to_csv(csv_path, index=False)
    print_head(df, title="HTML sentences")
    summarize_df(df, name="HTML sentences")
    print("[HTML] Saved sentences CSV:", csv_path)


# (iii) PDF/Word — text extraction (with optional OCR fallback)

def ocr_first_page(pdf_path: Path) -> str:
    if pytesseract is None or Image is None:
        print("[PDF] pytesseract/Pillow not installed. Skipping OCR.")
        return ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return ""
            pil_img = pdf.pages[0].to_image(resolution=300).original
            txt = pytesseract.image_to_string(pil_img)
            return txt.strip()
    except Exception as e:
        print("[PDF] OCR failed:", e)
        return ""

def run_pdf_part(pdf_url: str, outdir: Path) -> None:
    if pdfplumber is None:
        print("[PDF] pdfplumber not installed. Run: pip install pdfplumber")
        return
    print(f"\n[PDF] Downloading: {pdf_url}")
    headers = {"User-Agent": "Mozilla/5.0 (compatible; DSCI560-Lab2/1.0)"}
    r = requests.get(pdf_url, headers=headers, timeout=60)
    r.raise_for_status()

    pdf_path = outdir / "document.pdf"
    pdf_path.write_bytes(r.content)
    print("[PDF] Saved:", pdf_path)

    extracted_chunks = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:5]:  # limit to first 5 pages for lab
                txt = page.extract_text() or ""
                if txt.strip():
                    extracted_chunks.append(txt.strip())
    except Exception as e:
        print("[PDF] pdfplumber read error:", e)

    joined = "\n\n".join(extracted_chunks).strip()
    if not joined:
        print("[PDF] No selectable text found. Trying OCR on first page …")
        joined = ocr_first_page(pdf_path)

    if not joined:
        print("[PDF] No text could be extracted.")
        return

    # Save excerpt + paragraph CSV
    lines = [ln for ln in joined.splitlines() if ln.strip()]
    excerpt = "\n".join(lines[:120])
    txt_path = outdir / "pdf_text_excerpt.txt"
    txt_path.write_text(excerpt, encoding="utf-8")
    print("[PDF] Saved excerpt:", txt_path)

    paras = [p.strip() for p in re.split(r"\n\s*\n", joined) if p.strip()]
    df = pd.DataFrame({"paragraph": paras[:60]})
    csv_path = outdir / "pdf_paragraphs_sample.csv"
    df.to_csv(csv_path, index=False)
    print_head(df, title="PDF paragraphs")
    summarize_df(df, name="PDF paragraphs")
    print("[PDF] Saved paragraphs CSV:", csv_path)


def parse_args():
    ap = argparse.ArgumentParser(description="DSCI-560 Lab 2 — data exploration for three data types")
    ap.add_argument("--outdir", default="outputs", help="Output directory")

    # CSV params
    ap.add_argument("--ticker", default="AAPL", help="Ticker for CSV part (yfinance)")
    ap.add_argument("--period", default="1y", help="yfinance period (e.g., 1mo, 3mo, 1y)")
    ap.add_argument("--interval", default="1d", help="yfinance interval (e.g., 1d, 1wk)")

    # HTML param (use a stable HTML page; SEC filing HTML works well)
    ap.add_argument("--html_url",
                    default="https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm",
                    help="Public HTML page to extract text from")

    # PDF param (use a public PDF; IRS publications are stable)
    ap.add_argument("--pdf_url",
                    default="https://d18rn0p25nwr6d.cloudfront.net/CIK-0000320193/faab4555-c69b-438a-aaf7-e09305f87ca3.pdf",
                    help="Public PDF to extract text from")

    # what to run
    ap.add_argument("--run", choices=["all", "csv", "html", "pdf"], default="all",
                    help="Which part(s) to run")
    return ap.parse_args()

def main():
    args = parse_args()
    outdir = ensure_outdir(args.outdir)

    print("\n==============================")
    print(" DSCI-560 Lab 2: Data Exploration")
    print("==============================")

    if args.run in ("all", "csv"):
        run_csv_part(args.ticker, args.period, args.interval, outdir)

    if args.run in ("all", "html"):
        try:
            run_html_part(args.html_url, outdir)
        except Exception as e:
            print(f"[HTML] Error: {e}")

    if args.run in ("all", "pdf"):
        try:
            run_pdf_part(args.pdf_url, outdir)
        except Exception as e:
            print(f"[PDF] Error: {e}")

    print("\nDone. Check outputs in:", outdir.resolve())

if __name__ == "__main__":
    main()