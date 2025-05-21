from fastapi import APIRouter, UploadFile, File, Form

from app.core.response import CommonResponse
from app.services.interview_service import InterviewService

router = APIRouter()

@router.post("/interview/waiting-room")
async def get_landmarks(
    file: UploadFile = File(...),
    combineId: str = Form(...)
):
    result = await InterviewService.process_landmark(file, combineId)

    return CommonResponse.success_response("랜드 마크 기준점 계산 성공", result)