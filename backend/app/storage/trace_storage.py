
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

    return {
        "trace_id": trace_id,
        "trace_status": trace.get("status"),
        "failure_count": len(failed_spans),
        "failures": [
            {
                "step_name": span.get("step_name"),
                "error": span.get("error"),
                "latency_ms": span.get("latency_ms")
            }
            for span in failed_spans
        ]
    }
