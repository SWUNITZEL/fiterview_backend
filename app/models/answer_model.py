from typing import Optional, List, Tuple

from pydantic import BaseModel
from datetime import datetime

class Answer(BaseModel):
    id: Optional[str] = None
    interview_id: Optional[str] = None
    question_id: Optional[str] = None
    keyword: Optional[List[str]] = None
    answer: Optional[str] = None
    summary: Optional[str] = None
    aiAnalysis_comment: Optional[str] = None
    improved_answer: Optional[str] = None
    blind_rule_adherence: Optional[str] = None
    smile_ratio: Optional[float] = None
    gaze_down_count: Optional[int] = None
    gaze_points: Optional[List[Tuple[int, int]]] = None
    shoulder_tilt_count: Optional[int] = None
    turn_left_count: Optional[int] = None
    turn_right_count: Optional[int] = None
    video_url: Optional[str] = None
    speaking_speed: Optional[float] = None
    pitch_mean: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None