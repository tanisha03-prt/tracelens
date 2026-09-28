from fastapi import FastAPI
from .models.document import DocumentInput

app = FastAPI(title="TraceLens API") #Isse FastAPI application create hoti hai.


@app.get("/")
def home():
    return {"message": "TraceLens is running"}


@app.post("/pipeline/intake")
def intake(document: DocumentInput):
    return {
        "message": "Document received",
        "document": document
    }