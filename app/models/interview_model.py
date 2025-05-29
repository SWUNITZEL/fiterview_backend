from typing import Optional

from pydantic import BaseModel
from datetime import datetime

class Interview(BaseModel):
    combine_id: Optional[str] = None
    user_id: Optional[str] = None
    gesture_score: Optional[float] = 0.0
    expression_score: Optional[float] = 0.0
    posture_score: Optional[float] = 0.0
    stt_score: Optional[float] = 0.0
    pitch_score: Optional[float] = 0.0
    total_score: Optional[float] = 0.0
    ear: Optional[float] = 0.0
    smile_threshold: Optional[float] = 0.0
    avg_iris_ratio: Optional[float] = 0.0
    shoulder_distance: Optional[float] = 0.0
    head_x: Optional[float] = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None