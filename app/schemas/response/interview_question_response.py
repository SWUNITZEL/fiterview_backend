from pydantic import BaseModel
from pydantic.alias_generators import to_camel


class InterviewQuestionResponse(BaseModel):
    question_id: str
    type: str
    total_questions: int
    question_index: float
    question_text: str
    has_follow_up: bool

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True