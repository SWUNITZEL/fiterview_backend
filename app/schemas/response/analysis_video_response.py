from openai import BaseModel
from pydantic.alias_generators import to_camel


class AnalysisVideoResponse(BaseModel):
    interview_id: str
    answer_id: str
    question_id: str
    smile_ratio: float
    video_url: str

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True