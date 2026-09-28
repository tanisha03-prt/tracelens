from pydantic import BaseModel, Field


class DocumentInput(BaseModel):   # "TraceLens mein aane wala document in fields ka hona chahiye."
    document_id: str    #Har document ka unique ID hoga.
    raw_text: str = Field(min_length=1)    #Document ka actual text.
    # document ka text empty nhi ho sakta