from typing import Optional

from pydantic import BaseModel
from datetime import datetime

class Question(BaseModel):
    interview_id: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    attribute: Optional[str] = None
    persona: Optional[str] = None
    major: Optional[str] = None
    question: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None