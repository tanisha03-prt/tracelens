from pydantic import BaseModel
from typing import Any


class Span(BaseModel):
    step_name: str
    input: Any = None
    output: Any = None
    status: str
    latency_ms: float | None = None
    error: str | None = None


class Trace(BaseModel):
    trace_id: str
    status: str
    spans: list[Span] = []