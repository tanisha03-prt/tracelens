
from fastapi import FastAPI

from .models.document import DocumentInput
from .models.trace import Trace, Span
from .services.llm import (
    extract_document,
    classify_document,
    summarize_document
)

import uuid
import time


app = FastAPI(title="TraceLens API")


@app.get("/")
def home():
    return {"message": "TraceLens is running"}


@app.post("/pipeline/intake")
def intake(document: DocumentInput):

    # Create Trace
    trace_id = str(uuid.uuid4())

    trace = Trace(
        trace_id=trace_id,
        status="running",
        spans=[]
    )

    # Extraction
    start_time = time.perf_counter()

    try:
        extraction = extract_document(document.raw_text)

        latency = (time.perf_counter() - start_time) * 1000

        trace.spans.append(
            Span(
                step_name="extraction",
                input=document.raw_text,
                output=extraction.model_dump(),
                status="success",
                latency_ms=latency
            )
        )

    except Exception as e:
        latency = (time.perf_counter() - start_time) * 1000

        trace.spans.append(
            Span(
                step_name="extraction",
                input=document.raw_text,
                output=None,
                status="failed",
                latency_ms=latency,
                error=str(e)
            )
        )

        trace.status = "failed"

        return {
            "message": "Extraction failed",
            "document_id": document.document_id,
            "trace_id": trace.trace_id,
            "trace": trace
        }

    # Classification
    start_time = time.perf_counter()

    try:
        classification = classify_document(document.raw_text)

        latency = (time.perf_counter() - start_time) * 1000

        trace.spans.append(
            Span(
                step_name="classification",
                input=document.raw_text,
                output=classification.model_dump(),
                status="success",
                latency_ms=latency
            )
        )

    except Exception as e:
        latency = (time.perf_counter() - start_time) * 1000

        trace.spans.append(
            Span(
                step_name="classification",
                input=document.raw_text,
                output=None,
                status="failed",
                latency_ms=latency,
                error=str(e)
            )
        )

        trace.status = "failed"

        return {
            "message": "Classification failed",
            "document_id": document.document_id,
            "trace_id": trace.trace_id,
            "trace": trace
        }

    # Summarization
    start_time = time.perf_counter()

    try:
        summary = summarize_document(
            document.raw_text,
            classification.document_type
        )

        latency = (time.perf_counter() - start_time) * 1000

        trace.spans.append(
            Span(
                step_name="summarization",
                input=document.raw_text,
                output=summary.model_dump(),
                status="success",
                latency_ms=latency
            )
        )

    except Exception as e:
        latency = (time.perf_counter() - start_time) * 1000

        trace.spans.append(
            Span(
                step_name="summarization",
                input=document.raw_text,
                output=None,
                status="failed",
                latency_ms=latency,
                error=str(e)
            )
        )

        trace.status = "failed"

        return {
            "message": "Summarization failed",
            "document_id": document.document_id,
            "trace_id": trace.trace_id,
            "trace": trace
        }

    # All steps succeeded
    trace.status = "success"

    return {
        "message": "Document processed",
        "document_id": document.document_id,
        "trace_id": trace.trace_id,
        "extraction": extraction,
        "classification": classification,
        "summary": summary,
        "trace": trace
    }
