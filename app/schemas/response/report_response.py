from pydantic import BaseModel
from typing import List, Optional

class QuestionReport(BaseModel):
    answer_id: str
    question_id: str
    question: str
    intent: str
    answerText: str
    evaluation: List[str]  # 카테고리 제목 리스트
    goodExample: str  # 개선된 모범 답변
    summary: str  # 답변 총평
    followupQuestions: Optional[List[str]] = None
    videos: List[str] = []
    questionIndex: float

    class Config:
        extra = "allow"  # 예상 못한 필드도 통과. 이미 db 저장된 url 불러오기 위해 추가

class ReportResponse(BaseModel):
    report: List[QuestionReport]