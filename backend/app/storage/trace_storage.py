
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
        error = span.get("error") or "Unknown error"

        # Rule-based failure analysis
        if "Simulated extraction failure" in error:
            likely_cause = "Extraction was deliberately failed during testing"
            recommended_action = (
                "Remove the temporary test exception and retry the pipeline"
            )

        elif "JSON" in error or "json" in error:
            likely_cause = "The extraction response may not be valid JSON"
            recommended_action = (
                "Check the extraction response format before parsing it"
            )

        else:
            likely_cause = "The step failed; the exact cause is not yet classified"
            recommended_action = (
                "Inspect the error message and the failed step's input"
            )

        failures.append({
            "step_name": span.get("step_name"),
            "error": error,
            "latency_ms": span.get("latency_ms"),
            "likely_cause": likely_cause,
            "recommended_action": recommended_action
        })

    return {
        "trace_id": trace_id,
        "trace_status": trace.get("status"),
        "failure_count": len(failures),
        "failures": failures
    }

