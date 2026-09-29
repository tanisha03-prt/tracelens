from pydantic import BaseModel


class ClassificationResult(BaseModel):
    document_type: str