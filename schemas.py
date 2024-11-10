# schemas.py
from pydantic import BaseModel
from typing import Optional

class ScrapeRequest(BaseModel):
    alphabet: str
    num_pages: Optional[int] = 1
