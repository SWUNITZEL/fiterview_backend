from typing import Optional, List
from pydantic import BaseModel


class Document(BaseModel):
    user_id: Optional[str] = None
    content: Optional[str] = None
    grades: Optional[dict] = None
    features: Optional[str] = None
    type: Optional[str] = None
    hashtags: Optional[List[str]] = None
    explanation: Optional[str] = None
