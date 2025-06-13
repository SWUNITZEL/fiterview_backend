from openai import BaseModel
from pydantic.alias_generators import to_camel


class AnalysisVideoResponse(BaseModel):
    interview_id: str
    answer_id: str
    question_id: str
    smile_ratio: float
    gaze_down_count: int
    gaze_points : list
    blink_count : int
    shoulder_tilt_count: int
    turn_left_count: int
    turn_right_count: int
    video_url: str

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True