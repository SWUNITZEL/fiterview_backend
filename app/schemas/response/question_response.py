from pydantic import BaseModel
from typing import Optional

class QuestionOutput(BaseModel):
    questionIndex: int
    questionText: str
