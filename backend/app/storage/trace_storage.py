
import json
from pathlib import Path

from ..models.trace import Trace
from .trace_database import register_trace

# Folder where trace files will be stored
TRACES_DIR = Path(__file__).resolve().parent / "traces"



def save_trace(trace: Trace):
    # Create traces folder if it doesn't exist
    TRACES_DIR.mkdir(parents=True, exist_ok=True)

    # Create a filename using the trace ID
    file_path = TRACES_DIR / f"{trace.trace_id}.json"

    # Convert Trace object to a dictionary
    trace_data = trace.model_dump()

    # Save trace data as JSON
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(trace_data, file, indent=4, ensure_ascii=False)

    # Register the trace in SQLite database
    register_trace(
        trace_id=trace.trace_id,
        status=trace.status,
        file_path=str(file_path)
    )

    return str(file_path)



def get_trace(trace_id: str):
    file_path = TRACES_DIR / f"{trace_id}.json"

    if not file_path.exists():
        return None

    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)




# Failure category constants
CATEGORY_EXTRACTION_FAILURE = "EXTRACTION_FAILURE"
CATEGORY_INVALID_JSON = "INVALID_JSON"
CATEGORY_CLASSIFICATION_FAILURE = "CLASSIFICATION_FAILURE"
CATEGORY_SUMMARIZATION_FAILURE = "SUMMARIZATION_FAILURE"
CATEGORY_UNKNOWN_ERROR = "UNKNOWN_ERROR"


def categorize_failure(step_name: str | None, error: str | None) -> str:
    """Classifies a failed pipeline step into a consistent, deterministic category."""
    step = (step_name or "").strip().lower()
    err = (error or "").strip()
    err_lower = err.lower()

    # Rule 1: JSON parsing errors
    if "json" in err_lower or "expecting value" in err_lower or "unterminated string" in err_lower:
        return CATEGORY_INVALID_JSON

    # Rule 2: Step-based classification
    if step == "extraction":
        return CATEGORY_EXTRACTION_FAILURE
    elif step == "classification":
        return CATEGORY_CLASSIFICATION_FAILURE
    elif step == "summarization":
        return CATEGORY_SUMMARIZATION_FAILURE

    # Rule 3: Unknown or unrecognized error
    return CATEGORY_UNKNOWN_ERROR


def analyze_failure(trace_id: str):
    trace = get_trace(trace_id)

    if trace is None:
        return None

    failed_spans = [
        span for span in trace.get("spans", [])
        if span.get("status") == "failed"
    ]

    failures = []

    for span in failed_spans:
        step_name = span.get("step_name")
        error = span.get("error") or "Unknown error"

        # Deterministic failure category
        failure_category = categorize_failure(step_name, error)

        # Rule-based failure analysis for likely cause and recommendation
        if failure_category == CATEGORY_INVALID_JSON:
            likely_cause = "The extraction response may not be valid JSON"
            recommended_action = (
                "Check the extraction response format before parsing it"
            )

        elif failure_category == CATEGORY_EXTRACTION_FAILURE:
            if "Simulated extraction failure" in error:
                likely_cause = "Extraction was deliberately failed during testing"
                recommended_action = (
                    "Remove the temporary test exception and retry the pipeline"
                )
            else:
                likely_cause = "Extraction step failed while extracting document metadata"
                recommended_action = (
                    "Verify raw text format and extraction model output"
                )

        elif failure_category == CATEGORY_CLASSIFICATION_FAILURE:
            likely_cause = "Document classification step encountered an error"
            recommended_action = (
                "Inspect the document text and classification prompt"
            )

        elif failure_category == CATEGORY_SUMMARIZATION_FAILURE:
            likely_cause = "Document summarization step encountered an error"
            recommended_action = (
                "Verify document type and summarization input parameters"
            )

        else:
            likely_cause = "The step failed; the exact cause is not yet classified"
            recommended_action = (
                "Inspect the error message and the failed step's input"
            )

        failures.append({
            "step_name": step_name,
            "failure_category": failure_category,
            "error": error,
            "latency_ms": span.get("latency_ms"),
            "likely_cause": likely_cause,
            "recommended_action": recommended_action
        })

    return {
        "trace_id": trace_id,
        "trace_status": trace.get("status"),
        "failure_count": len(failures),
        "failure_category": failures[0]["failure_category"] if failures else None,
        "failures": failures
    }

