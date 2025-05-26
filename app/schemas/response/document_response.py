from pydantic import BaseModel
from pydantic.alias_generators import to_camel


# 생활기록부 분석 내용 응답
class DocumentResponse(BaseModel):
    grades: dict
    type: str
    hashtags: list[str]
    explanation: str