from datetime import date
from typing import Optional

from pydantic import BaseModel
from pydantic.alias_generators import to_camel


class CreateCombineRequest(BaseModel):
    university: str
    department: str
    question_count: int
    interview_date: Optional[date]
    persona: list[str]

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True