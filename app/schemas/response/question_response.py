from pydantic import BaseModel
from typing import Optional

class QuestionOutput(BaseModel):
    questionIndex: int
    questionText: str
    hasFollowUp: Optional[bool] = None
    followUpText: Optional[str] = None
    answerId: Optional[str] = None
