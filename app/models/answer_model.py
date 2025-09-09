from typing import Optional, List, Tuple, Union

from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId

class GazePoint(BaseModel):
    x: int
    y: int
    time: datetime

class Answer(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    interview_id: Optional[str] = None
    question_id: Optional[str] = None
    answer: Optional[str] = None
    summary: Optional[str] = None
    aiAnalysis_comment: Optional[str] = None
    improved_answer: Optional[str] = None
    blind_rule_adherence: Optional[str] = None
    blinks_per_minute: Optional[float] = None
    smile_ratio: Optional[float] = None
    gaze_down_count: Optional[int] = None
    gaze_points: Optional[List[GazePoint]] = None
    shoulder_tilt_count: Optional[int] = None
    turn_left_count: Optional[int] = None
    turn_right_count: Optional[int] = None
    video_url: Optional[str] = None
    speaking_speed: Optional[float] = None
    pitch_mean: Optional[float] = None
    frequently_used_words: List[Tuple[str, int]] = None
    hesitant_list: List[str] = None
    hesitant_score: int = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str},
        "arbitrary_types_allowed": True,
    }