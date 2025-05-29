from fastapi import APIRouter, UploadFile, File, Form, Path

from app.core.response import CommonResponse
from app.schemas.request.create_combine_request import CreateCombineRequest
from app.services.answer_service import AnswerService
from app.services.combine_service import CombineService
from app.services.interview_service import InterviewService

router = APIRouter()

@router.post("/interview/waiting-room")
async def get_landmarks(
    file: UploadFile = File(...),
    combine_id: str = Form(..., alias="combineId")
):
    result = await InterviewService.process_landmark(file, combine_id)

    return CommonResponse.success_response("랜드 마크 기준점 계산 성공", result)

@router.post("/interview/start")
async def create_combine(
    create_combine_request: CreateCombineRequest
):
    result = await CombineService.create_combine(create_combine_request)

    return CommonResponse.success_response("면접 조합 생성 성공", result)

@router.post("/interview/{interview_id}/analysis-video")
async def analysis_video(
        file: UploadFile = File(...),
        question_id: str = Form(..., alias="questionId"),
        interview_id: str = Path(...)
):
    result = await AnswerService.analysis_answer_video(file, interview_id, question_id)

    return CommonResponse.success_response("영상 분석 성공", result)