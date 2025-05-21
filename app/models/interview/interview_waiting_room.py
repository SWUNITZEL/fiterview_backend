from bson import ObjectId
from pydantic import BaseModel


# 영상 분석 기준점
class InterviewWaitingRoomResponse(BaseModel):
    interviewId: str
    ear: float
    smileThreshold: float
    avgIrisRatio: float