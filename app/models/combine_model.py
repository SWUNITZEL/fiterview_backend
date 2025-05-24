from typing import Optional

from pydantic import BaseModel
from datetime import datetime

class Combine(BaseModel):
    document_id: Optional[str] = None
    user_d: Optional[str] = None
    university: Optional[str] = None
    department: Optional[str] = None
    interview_date: Optional[datetime] = None
    question_count: Optional[int] = 0
    persona: Optional[list[str]] = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None