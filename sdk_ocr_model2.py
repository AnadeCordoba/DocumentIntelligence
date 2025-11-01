import os
import re
import time
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from openai import AzureOpenAI


load_dotenv()

AZURE_DOCINTEL_ENDPOINT = os.getenv("AZURE_DOCINTEL_ENDPOINT")
AZURE_DOCINTEL_KEY = os.getenv("AZURE_DOCINTEL_KEY")
MODEL_READ = os.getenv("MODEL_READ")


DOCS_DIR = Path(os.getenv("JPG_DIR"))
OUTPUT_DIR = Path(os.getenv("RESULT_TXT"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT") 
AZURE_KEY = os.getenv("AZURE_KEY")
API_VERSION = os.getenv("API_VERSION")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")


PROMPT = (
    "You are an OCR text corrector. STRICT RULES:\n"
    "1) Do not add, delete, or reorder any information; DO NOT fill in gaps or guess missing data.\n"
    "2) Only fix obvious OCR mistakes: misrecognized characters (l/1, O/0), broken words, accents, spacing, and punctuation.\n"
    "3) Keep all numbers, dates, proper names, and sentence order exactly as they appear.\n"
    "4) Preserve line breaks when they indicate paragraph separation.\n"
    "5) If something is unclear, leave it as is or mark it with '???', but DO NOT invent anything.\n"
    "Return only the corrected text, with no explanations."
)




ocr_client = DocumentIntelligenceClient(
    endpoint=AZURE_DOCINTEL_ENDPOINT,
    credential=AzureKeyCredential(AZURE_DOCINTEL_KEY),
)

llm_client = AzureOpenAI(
    api_version=API_VERSION,
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_KEY,)

def normalize_ocr_text(text: str, strip_noise: bool = True) -> str:
    """
    Convierte texto OCR línea a línea en párrafos legibles:
    - repara cortes de palabra con guion al final de línea (“sol-\ntero” -> “soltero”).
    - une líneas consecutivas en un mismo párrafo si no acaban en . ! ? :
    - normaliza espacios.
    """

    lines = text.splitlines()

    if strip_noise:
        lines = [
            ln.strip()
            for ln in lines
            if not re.fullmatch(r"[\W_]*\d{1,4}[\W_]*", ln.strip()) and not re.fullmatch(r"[\W_]{1,3}", ln.strip())
        ]
    else:
        lines = [ln.strip() for ln in lines]


    joined = "\n".join(lines)
    joined = re.sub(r"-\n(\w)", r"\1", joined)

    normalized = re.sub(r"(?<![.!?:])\n(?!\n)", " ", joined)
    normalized = re.sub(r"[ \t]{2,}", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)

    return normalized.strip()


def clean_text_with_llm(raw_text: str) -> str:
    """ Send OCR text to Azure OpenAI for cleaning according to PROMPT. """

    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": raw_text.strip()},
    ]

    try:
        resp = llm_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=messages,
            temperature=0.2,
            top_p=1.0,
        )
    except Exception as e:
        print(f"Error calling Azure OpenAI: {e}")
        raise e
        
    return resp.choices[0].message.content.strip()




def analyze_and_clean(doc_path: Path) -> None:
    """analyze and clean document text"""

    start = time.time()

    body = AnalyzeDocumentRequest(bytes_source=doc_path.read_bytes())
    poller = ocr_client.begin_analyze_document(MODEL_READ, body)
    result = poller.result()

    pages = []
    for page in result.pages:
        lines = [line.content for line in page.lines] if page.lines else []
        pages.append("\n".join(lines))
    raw_text = "\n\n".join(pages)


    normalized_text = normalize_ocr_text(raw_text)

    cleaned_text = clean_text_with_llm(normalized_text)

    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    output_path = OUTPUT_DIR / f"{doc_path.stem}_{timestamp}.txt"
    output_path.write_text(cleaned_text, encoding="utf-8")

    elapsed = time.time() - start
    print(f"{doc_path.name} - {elapsed:.2f} s.")


def main() -> None:
    exts = {".pdf", ".png", ".jpg", ".jpeg"}
    files = sorted(p for p in DOCS_DIR.iterdir() if p.is_file() and p.suffix.lower() in exts)


    total_start = time.time()
    for f in files:
        try:
            analyze_and_clean(f)
        except Exception as e:
            print(f"Error {f.name}: {e}")

    total_elapsed = time.time() - total_start
    print(f"Time: {total_elapsed:.2f} s")


if __name__ == "__main__":
    main()
