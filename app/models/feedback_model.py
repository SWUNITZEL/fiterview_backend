from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Feedback(BaseModel):
    question_id: str
    answer_id: str
    major: str
    feedback_text: Optional[str] = None
    created_at: Optional[datetime] = None
