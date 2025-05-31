from pydantic import BaseModel
from pydantic.alias_generators import to_camel


# 영상 분석 기준점
class InterviewWaitingRoomResponse(BaseModel):
    interview_id: str
    ear: float
    smile_threshold: float
    avg_iris_ratio: float
    shoulder_diff: float
    head_rotation: float

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True