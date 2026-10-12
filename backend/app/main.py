

from fastapi import FastAPI, HTTPException

import uuid
import time

from .models.document import DocumentInput
from .models.trace import Trace, Span
from .services.llm import (
    extract_document,
    classify_document,
    summarize_document
)
from .storage.trace_storage import save_trace, get_trace, analyze_failure
from .storage.trace_database import list_traces


app = FastAPI(title="TraceLens API")


@app.get("/")
def home():
    return {"message": "TraceLens is running"}


@app.get("/traces/{trace_id}")
def retrieve_trace(trace_id: str):
    trace = get_trace(trace_id)

    if trace is None:
        raise HTTPException(
            status_code=404,
            detail=f"Trace {trace_id} not found"
        )
    

    return trace

@app.get("/traces")
def get_all_traces(status: str | None = None):
    return list_traces(status)


@app.get("/traces/{trace_id}/analysis")
def get_failure_analysis(trace_id: str):
    analysis = analyze_failure(trace_id)

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail=f"Trace {trace_id} not found"
        )

    return analysis



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
        save_trace(trace)

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
        save_trace(trace)

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
        save_trace(trace)

        return {
            "message": "Summarization failed",
            "document_id": document.document_id,
            "trace_id": trace.trace_id,
            "trace": trace
        }

    # All steps succeeded
    trace.status = "success"
    save_trace(trace)


    return {
        "message": "Document processed",
        "document_id": document.document_id,
        "trace_id": trace.trace_id,
        "extraction": extraction,
        "classification": classification,
        "summary": summary,
        "trace": trace
    }
