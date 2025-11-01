import os, re, time, json
import pandas as pd
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
MODEL_READ = os.getenv("MODEL_READ") or "prebuilt-read"


DOCS_DIR = Path(os.getenv("OCR_LIBROS"))
RESULT_LIBROS = Path(os.getenv("RESULT_LIBROS"))
RESULT_LIBROS.mkdir(parents=True, exist_ok=True)


AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT") 
AZURE_KEY = os.getenv("AZURE_KEY")
API_VERSION = os.getenv("API_VERSION")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")


PROMPT = (
    "Eres un bibliotecario experto. Analiza texto OCR de portadas o lomos de libros "
    "y DEVUELVE exclusivamente un JSON válido con una lista de objetos.\n"
    "Cada objeto debe tener estas claves:\n"
    '  - \"Título\": string\n'
    '  - \"Autor\": lista de strings\n'
    '  - \"Número\": string o \"-\"\n'
    "NO inventes datos, usa '-' si faltan. No añadas texto extra ni explicaciones, solo JSON."
)


ocr_client = DocumentIntelligenceClient(
    endpoint=AZURE_DOCINTEL_ENDPOINT,
    credential=AzureKeyCredential(AZURE_DOCINTEL_KEY),
)
llm_client = AzureOpenAI(
    api_version=API_VERSION,
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_KEY,
)

def extract_books_with_llm(raw_text: str) -> list[dict]:
    """send OCR text to LLM and parse the JSON response."""
    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": raw_text.strip()},
    ]
    resp = llm_client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT, messages=messages, temperature=0
    )
    output = resp.choices[0].message.content.strip()

    try:
        data = json.loads(output)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list):
                    return v
    except Exception:
        pass


    m = re.search(r"\[\s*{.*}\s*\]", output, flags=re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass

    return [{"Título": "-", "Autor": [], "Número": "-"}]

def analyze_one(doc_path: Path) -> list[dict]:
    """Ejecuta OCR con prebuilt-read y llama al LLM."""
    body = AnalyzeDocumentRequest(bytes_source=doc_path.read_bytes())
    poller = ocr_client.begin_analyze_document(MODEL_READ, body)
    result = poller.result()

    text_pages = []
    for page in result.pages:
        lines = [line.content for line in page.lines] if page.lines else []
        text_pages.append("\n".join(lines))
    raw_text = "\n\n".join(text_pages)

    return extract_books_with_llm(raw_text)

def main():
    exts = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
    files = sorted(p for p in DOCS_DIR.iterdir() if p.is_file() and p.suffix.lower() in exts)

    rows = []
    t0 = time.time()
    for f in files:
        try:
            books = analyze_one(f)
            for b in books:
                title = (b.get("Título") or "").strip()
                authors = b.get("Autor") or []
                if isinstance(authors, str):
                    authors = [authors]
                editorial = (b.get("Editorial") or "-").strip() or "-"
                numero = (b.get("Número") or "-").strip() or "-"
                rows.append({
                    "filename": f.name,
                    "title": title,
                    "authors": "; ".join(a.strip() for a in authors if str(a).strip()),
                    "numero": numero,
                })
        except Exception as e:
            print(f"Error{f.name}: {e}")
            rows.append({"title": "", "authors": "", "numero": "-"})

    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    out_csv = RESULT_LIBROS / f"libros_{ts}.csv"

    df = pd.DataFrame(rows, columns=["filename", "title", "authors", "numero"])
    df.to_csv(out_csv, index=False, encoding="utf-8")

if __name__ == "__main__":
    main()
