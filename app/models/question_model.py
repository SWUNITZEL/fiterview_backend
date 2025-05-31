from typing import Optional

from pydantic import BaseModel
from datetime import datetime



class Question(BaseModel):
    id: Optional[str] = None
    interview_id: Optional[str] = None
    question_text: Optional[str] = None
    question_index: Optional[int] = None
    total_questions: Optional[int] = None
    persona: Optional[str] = None
    major: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None