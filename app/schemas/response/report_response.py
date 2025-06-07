from pydantic import BaseModel
from typing import List, Optional

class QuestionReport(BaseModel):
    question: str
    intent: str
    answerSummary: str
    answerImprovement: str
    followupQuestions: Optional[List[str]] = None

class ReportResponse(BaseModel):
    interviewType: str
    report: List[QuestionReport]