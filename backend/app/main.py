from fastapi import FastAPI

from .models.document import DocumentInput
from .services.llm import extract_document, classify_document


app = FastAPI(title="TraceLens API")


@app.get("/")
def home():
    return {"message": "TraceLens is running"}


@app.post("/pipeline/intake")
def intake(document: DocumentInput):
    extraction = extract_document(document.raw_text)
    classification = classify_document(document.raw_text)

    return {
        "message": "Document processed",
        "document_id": document.document_id,
        "extraction": extraction,
        "classification": classification
    }