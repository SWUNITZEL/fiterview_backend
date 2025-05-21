from typing import Optional

from pydantic import BaseModel
from datetime import datetime

class Interview(BaseModel):
    combineId: Optional[str] = None
    userId: Optional[str] = None
    gestureScore: Optional[float] = 0.0
    expressionScore: Optional[float] = 0.0
    postureScore: Optional[float] = 0.0
    sttScore: Optional[float] = 0.0
    pitchScore: Optional[float] = 0.0
    totalScore: Optional[float] = 0.0
    ear: Optional[float] = 0.0
    smileThreshold: Optional[float] = 0.0
    avgIrisRatio: Optional[float] = 0.0
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None