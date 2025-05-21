from typing import Optional

from pydantic import BaseModel
from datetime import datetime

class Question(BaseModel):
    interviewId: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    attribute: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None