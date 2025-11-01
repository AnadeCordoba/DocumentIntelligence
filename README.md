# Azure Document Intelligence — Procesamiento y Extracción de Información

Este repositorio contiene una serie de scripts en Python que demuestran cómo utilizar el **SDK de Azure Document Intelligence (antes Form Recognizer)** para analizar documentos de distintos tipos —PDF, JPG, PNG— y convertirlos en **datos estructurados listos para su análisis**.

Los ejemplos incluyen tanto el uso de **modelos preentrenados** (modelo "prebuilt-invoice") como **OCR** ("prebuilt-read") de Document Intelligence Studio.  

---

## 📂 Estructura del proyecto

| Archivo | Descripción |
|----------|--------------|
| `sdk_facturas.py` | Analiza facturas utilizando el modelo preentrenado `prebuilt-invoice`. Extrae campos clave como proveedor, cliente, fecha, total, IVA, etc. y los exporta a CSV. |
| `sdk_ocr.py` | Realiza OCR sobre documentos o imágenes utilizando el modelo `prebuilt-read`. Convierte texto manuscrito o impreso en texto digital. |
| `sdk_ocr_model2.py` | Realiza OCR que combina el reconocimiento de texto con un **modelo LLM de Azure OpenAI**, para mejorar la extracción a un tipo de documento concreto. |
| `sdk_ocr_libros.py` | Realiza OCR que combina el reconocimiento de texto con un **modelo LLM de Azure OpenAI**. Extrayendo información de libros a partir de una foto, título, autor y número. Con la salida de los datos estructurados en CSV. |

---

## ⚙️ Requisitos previos

Antes de ejecutar los scripts, asegúrate de tener:

1. Una cuenta activa en **Azure** con el servicio **Document Intelligence** creado. 

#### Si no dispones de cuenta, puedes crear una desde Azure Free Account.
- La suscripción gratuita de 30 días de uso sin coste y 200 USD en crédito, suficientes para probar Document Intelligence, Azure OpenAI y otros servicios de IA en la nube. Más información visita [Azure Document Intelligence](https://azure.microsoft.com/es-es/pricing/purchase-options/azure-account?icid=azurefreeaccount).

2. Las variables de entorno configuradas en un archivo `.env`:

   ```bash
   AZURE_DOCINTEL_ENDPOINT="https://<tu-endpoint>.cognitiveservices.azure.com/"
   AZURE_DOCINTEL_KEY="<tu-clave-de-servicio>"
   MODEL="prebuilt-invoice"
   FACTURAS="<ruta/a/carpeta_facturas>"
   RESULT_CSV="<ruta/a/carpeta_facturas/resultados>"
   MODEL_READ="prebuilt-read"
   OCR_DIR="<ruta/a/carpeta_OCR>"
   RESULT_OCR="<ruta/a/carpeta_OCR/resultados>"
   JPG_DIR="<ruta/a/carpeta_OCR_MODEL>"
   OCR_LIBROS="<ruta/a/carpeta_libros>"
   RESULT_TXT="<ruta/a/carpeta_OCR_MODEL/resultados>"
   RESULT_LIBROS="<ruta/a/carpeta_libros/resultados>"
   
   # Para el modelo LLM:
   OPENAI_API_KEY="<tu-clave-openai>"
   OPENAI_MODEL="<modelo-llm>"
   AZURE_ENDPOINT="<endpoint-openai>"
   AZURE_KEY="<clave-openai>"
   API_VERSION="<versión-api>"
   AZURE_OPENAI_DEPLOYMENT="<nombre-del-despliegue>"


## ⚙️ Requisitos

Python 3.11+ y las siguientes dependencias instaladas:

```bash
pip install -r requirements.txt
```

## Ejecución de los scripts

**sdk_facturas.py**

Analiza facturas PDF, JPG y extrae los campos principales:


```bash
python sdk_facturas.py
```

- El resultado se guarda en un archivo CSV con formato:
filename,invoice_id,vendor_name,customer_name,invoice_date,due_date,subtotal,total_tax,invoice_total,payment_term,description


**sdk_ocr.py**

Convierte texto manuscrito o impreso en texto digital:

```bash
python sdk_ocr.py
```

Digitaliza textos y realizar búsquedas o análisis posteriores.

**sdk_ocr_model2.py**

Utiliza un modelo OCR read combinado con un modelo LLM para mejorar la precisión:

```bash
python sdk_ocr_model2.py
```

**sdk_ocr_libros.py**

Analiza fotos de lomo de libros para hacer inventario:

```bash
python sdk_ocr_libros.py
```

- El resultado se guarda en un archivo CSV con formato:
title,authors,numero

## Lógica general
Todos los scripts siguen un flujo similar:

Carga de credenciales desde .env.

Inicialización del cliente de Document Intelligence:
```python
client = DocumentIntelligenceClient(endpoint, AzureKeyCredential(api_key))
```

Envío del documento al modelo mediante:
```
poller = client.begin_analyze_document(model_id, AnalyzeDocumentRequest(url_source=file_url))
result = poller.result()
```

Extracción de los campos de interés y su conversión a CSV o texto plano.

---

## Buenas prácticas y seguridad de datos

- No subir nunca el archivo .env a GitHub (esto se puede evitar añadiendo `.env` a `.gitignore`).

- Si los documentos contienen información personal o sensible, anonimízala antes de procesarla y evita subirlo a repositorios.

---

## Recursos empleados

 - Azure Document Intelligence SDK (Python)
 - Azure OpenAI Service (LLM)
 - Suscripción gratuita de Azure (Ofrece 30 días de uso gratuito y 200 USD de crédito para probar Document Intelligence y Azure OpenAI.)

## Documentación a consultar


- [Suscripción gratuita Azure](https://azure.microsoft.com/es-es/pricing/purchase-options/azure-account?icid=azurefreeaccount)
- [Document Intellingece](https://learn.microsoft.com/es-es/azure/ai-services/document-intelligence/?view=doc-intel-4.0.0)
- [Azure OpenAI Service](https://azure.microsoft.com/es-es/products/ai-foundry/models/openai/)


---




Proyecto desarrollado por Ana de Córdoba.


