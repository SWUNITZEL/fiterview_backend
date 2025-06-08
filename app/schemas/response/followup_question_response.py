from pydantic import BaseModel
from typing import List

class FollowupQuestionResponse(BaseModel):
    answerId: str
    originalAnswer: str
    followupQuestions: List[str] 