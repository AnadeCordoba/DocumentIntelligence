from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from dotenv import load_dotenv
from pathlib import Path
import os
import time
from datetime import datetime


load_dotenv()
ENDPOINT = os.getenv("AZURE_DOCINTEL_ENDPOINT")
KEY = os.getenv("AZURE_DOCINTEL_KEY")
DOCS_DIR = Path(os.getenv("OCR_DIR"))  
OUTPUT_DIR = Path(os.getenv("RESULT_OCR"))  
MODEL_READ = os.getenv("MODEL_READ")

client = DocumentIntelligenceClient(endpoint=ENDPOINT, credential=AzureKeyCredential(KEY))



def analyze_one(doc_path: Path):
    """Analyze a handmade document and save the extracted text to a file."""
    start_time = time.time()

    body = AnalyzeDocumentRequest(bytes_source=doc_path.read_bytes())
    poller = client.begin_analyze_document(MODEL_READ, body)
    result = poller.result()
    elapsed = time.time() - start_time
    print(f"{doc_path.name} - {elapsed:.2f} s.")

    text_pages = []
    for page in result.pages:
        lines = [line.content for line in page.lines]
        text_pages.append("\n".join(lines))
    full_text = "\n\n".join(text_pages)

    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    output_path = OUTPUT_DIR / f"{doc_path.stem}_{timestamp}.txt"
    output_path.write_text(full_text, encoding="utf-8")
    



def main():
    exts = {".pdf", ".png", ".jpg", ".jpeg"}
    files = sorted(p for p in DOCS_DIR.iterdir() if p.is_file() and p.suffix.lower() in exts)

    total_start = time.time()
    for f in files:
        try:
            analyze_one(f)
        except Exception as e:
            print(f"Error {f.name}: {e}")

    total_elapsed = time.time() - total_start
    print(f"Time {total_elapsed:.2f} s")


if __name__ == "__main__":
    main()
