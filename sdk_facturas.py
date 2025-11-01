from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
import os
import pandas as pd
import time


load_dotenv()
ENDPOINT = os.getenv("AZURE_DOCINTEL_ENDPOINT")
KEY = os.getenv("AZURE_DOCINTEL_KEY")
FACTURAS_DIR = Path(os.getenv("FACTURAS"))
RESULT_CSV = Path(os.getenv("RESULT_CSV"))
MODEL = os.getenv("MODEL")


client = DocumentIntelligenceClient(endpoint=ENDPOINT, credential=AzureKeyCredential(KEY))

def fval(f):
    """Extract the value from a field, handling different possible types."""
    if not f:
        return ""
    if hasattr(f, "value_currency") and f.value_currency is not None:
        return f.value_currency.amount
    if hasattr(f, "value_number") and f.value_number is not None:
        return f.value_number
    if hasattr(f, "value_date") and f.value_date is not None:
        return f.value_date
    if hasattr(f, "value_string") and f.value_string is not None:
        return f.value_string
    return getattr(f, "content", "")

def analyze_one(pdf_path: Path):
    """Return a single row with all concatenated descriptions."""
    start_time = time.time()
    body = AnalyzeDocumentRequest(bytes_source=pdf_path.read_bytes())
    poller = client.begin_analyze_document(MODEL, body)
    result = poller.result()
    
    print(result)
    
    elapsed = time.time() - start_time
    print(f"{pdf_path.name} - {elapsed:.2f} s.")
    
    doc = result.documents[0]
    fields = doc.fields
    

    descriptions = []
    items_field = fields.get("Items")
    items_array = items_field.value_array if (items_field and items_field.value_array) else []
    for it in items_array:
        obj = it.value_object
        desc = fval(obj.get("Description")) if obj else ""
        if desc:
            descriptions.append(str(desc))
    description_joined = "; ".join(descriptions)

    row = {
        "filename":      pdf_path.name,
        "invoice_id":    fval(fields.get("InvoiceId")),
        "vendor_name":   fval(fields.get("VendorName")),
        "customer_name": fval(fields.get("CustomerName")),
        "invoice_date":  fval(fields.get("InvoiceDate")),
        "due_date":      fval(fields.get("DueDate")),
        "subtotal":      fval(fields.get("SubTotal")),
        "total_tax":     fval(fields.get("TotalTax")),
        "invoice_total": fval(fields.get("InvoiceTotal")),
        "description":   description_joined,
    }
    return row

def main():

    exts = {".pdf", ".png", ".jpg", ".jpeg"}
    files = sorted(
        p for p in FACTURAS_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in exts
    )

    rows = []
    total_start = time.time()
    for p in files:
        r = analyze_one(p)
        if r:
            rows.append(r)

    total_elapsed = time.time() - total_start
    print(f"Time:{total_elapsed:.2f} s.")

    df = pd.DataFrame(rows, columns=[
        "filename","invoice_id","vendor_name","customer_name",
        "invoice_date","due_date","subtotal","total_tax",
        "invoice_total","description"
    ])


    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    out_csv = RESULT_CSV / f"{timestamp}.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
