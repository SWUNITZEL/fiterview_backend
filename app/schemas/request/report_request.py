from pydantic import BaseModel

class ReportRequest(BaseModel):
    interviewType: str  # "essay" 또는 "self_intro" 등
