from typing import Optional

from pydantic import BaseModel
from datetime import datetime

class Combine(BaseModel):
    documentId: Optional[str] = None
    userId: Optional[str] = None
    university: Optional[str] = None
    department: Optional[str] = None
    interviewDate: Optional[datetime] = None
    questionCount: Optional[int] = 0
    persona: Optional[str] = 0.0
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None