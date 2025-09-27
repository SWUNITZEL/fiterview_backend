from pydantic import BaseModel
from typing import Optional, List

from pydantic.alias_generators import to_camel


class QuestionOutput(BaseModel):
    question_index: int
    question_text: str

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
        populate_by_name=True
        from_attributes = True


class CreatePersonaQuestionResponse(BaseModel):
    # persona_label: str
    # department: str
    questions: List[QuestionOutput]

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True