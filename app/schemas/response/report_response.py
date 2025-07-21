from pydantic import BaseModel
from typing import List, Optional

class QuestionReport(BaseModel):
    question: str
    intent: str
    answerText: str
    evaluation: List[str]  # 카테고리 제목 리스트
    goodExample: str  # 개선된 모범 답변
    summary: str  # 답변 총평
    followupQuestions: Optional[List[str]] = None
    videos: List[str] = []

class ReportResponse(BaseModel):
    report: List[QuestionReport]