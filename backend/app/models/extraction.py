from pydantic import BaseModel


class ExtractionResult(BaseModel):
    company: str | None = None
    date: str | None = None
    amount: float | None = None
    currency: str | None = None
    payment_terms: str | None = None