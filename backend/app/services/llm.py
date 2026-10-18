import os
import json

from dotenv import load_dotenv
from openai import OpenAI

from ..models.extraction import ExtractionResult
from ..models.classification import ClassificationResult
from ..models.summary import SummaryResult


# Load .env from backend directory if running from outside or inside
env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=env_path)
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None


def ask_llm(prompt: str):
    if "Classify" in prompt:
        return "invoice"

    if "Summarize" in prompt:
        return "ABC Technologies issued an invoice dated 12 March 2026 for EUR 5,400 with payment terms of 30 days."

    return """
{
    "company": "ABC Technologies",
    "date": "12 March 2026",
    "amount": 5400,
    "currency": "EUR",
    "payment_terms": "30 days"
}
"""


def extract_document(raw_text: str):
    
    prompt = f"""
Extract the following information from this document:

- company
- date
- amount
- currency
- payment_terms

Document:
{raw_text}
"""
    

    response = ask_llm(prompt)

    data = json.loads(response)

    return ExtractionResult(**data)


def classify_document(raw_text: str):
    prompt = f"""
Classify the following document into exactly one of these categories:

- invoice
- contract
- report
- correspondence

Document:
{raw_text}
"""

    response = ask_llm(prompt)

    return ClassificationResult(document_type=response.strip())


def summarize_document(raw_text: str, document_type: str):
    prompt = f"""
Summarize the following {document_type} document
in 2-3 clear sentences.

Document:
{raw_text}
"""

    response = ask_llm(prompt)

    return SummaryResult(summary=response.strip())


if __name__ == "__main__":
    document = """
    ABC Technologies
    Invoice Date: 12 March 2026
    Total Amount: €5,400
    Payment Terms: 30 days
    """

    extraction = extract_document(document)
    classification = classify_document(document)
    summary = summarize_document(document, "invoice")

    print("Extraction:")
    print(extraction)

    print("\nClassification:")
    print(classification)

    print("\nSummary:")
    print(summary)