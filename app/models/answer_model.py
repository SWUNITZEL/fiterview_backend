from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime

class Answer(BaseModel):
    interviewId: Optional[str] = None
    questionId: Optional[str] = None
    keyword: Optional[List[str]] = None
    answer: Optional[str] = None
    summary: Optional[str] = None
    aiAnalysisComment: Optional[str] = None
    improvedAnswer: Optional[str] = None
    blindRuleAdherence: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None