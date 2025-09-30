from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime



class Question(BaseModel):
    id: Optional[str] = None
    interview_id: Optional[str] = None
    question_text: Optional[str] = None
    question_index: Optional[float] = None
    total_questions: Optional[int] = None
    persona: Optional[List[str]] = None
    major: Optional[str] = None
    university: Optional[str] = None # 대학 추가
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    comment: Optional[str] = None