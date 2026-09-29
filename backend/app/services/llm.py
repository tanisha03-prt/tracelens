import os
import json

from dotenv import load_dotenv
from openai import OpenAI

from ..models.extraction import ExtractionResult
from ..models.classification import ClassificationResult


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY is not set")

client = OpenAI(api_key=api_key)


def ask_llm(prompt: str):
    if "Classify" in prompt:
        return "invoice"

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


if __name__ == "__main__":
    document = """
    ABC Technologies
    Invoice Date: 12 March 2026
    Total Amount: €5,400
    Payment Terms: 30 days
    """

    extraction = extract_document(document)
    classification = classify_document(document)

    print("Extraction:")
    print(extraction)

    print("\nClassification:")
    print(classification)