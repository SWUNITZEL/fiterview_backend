from pydantic import BaseModel
from typing import List

class QuestionInput(BaseModel):
    questionId: str
    answerId: str

class ReportRequest(BaseModel):
    interviewId: str
    interviewType: str  # "essay" 또는 "self_intro" 등
    questions: List[QuestionInput]
