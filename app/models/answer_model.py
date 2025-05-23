from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime

class Answer(BaseModel):
    interview_id: Optional[str] = None
    question_id: Optional[str] = None
    keyword: Optional[List[str]] = None
    answer: Optional[str] = None
    summary: Optional[str] = None
    aiAnalysis_comment: Optional[str] = None
    improved_answer: Optional[str] = None
    blind_rule_adherence: Optional[str] = None
    video_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None