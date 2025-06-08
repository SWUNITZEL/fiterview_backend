from typing import Annotated
from fastapi import APIRouter, UploadFile, File, Form, Path, Depends, HTTPException
from app.core.response import CommonResponse
from app.models.user_model import User
from app.schemas.request.create_combine_request import CreateCombineRequest
from app.schemas.response.followup_question_response import FollowupQuestionResponse
from app.services.answer_service import AnswerService
from app.services.auth_service import AuthService
from app.services.combine_service import CombineService
from app.services.interview_service import InterviewService
from app.services.followup_question_service import FollowupQuestionService
from app.core.exceptions.custom import InterviewNotFoundException

auth_service = AuthService()
router = APIRouter(dependencies=[Depends(auth_service.get_current_user)])

@router.post("/interview/waiting-room")
async def get_landmarks(
    file: UploadFile = File(...),
    combine_id: str = Form(..., alias="combineId")
):
    print("start")
    result = await InterviewService.process_landmark(file, combine_id)

    print("end")
    return CommonResponse.success_response("랜드 마크 기준점 계산 성공", result)

@router.post("/interview/start")
async def create_combine(
    current_user: Annotated[User, Depends(auth_service.get_current_user)],
    create_combine_request: CreateCombineRequest
):
    result = await CombineService.create_combine(create_combine_request, current_user.get("email"))

    return CommonResponse.success_response("면접 조합 생성 성공", result)

@router.post("/interview/{interview_id}/analysis-video")
async def analysis_video(
        file: UploadFile = File(...),
        question_id: str = Form(..., alias="questionId"),
        interview_id: str = Path(...)
):
    result = await AnswerService.analysis_answer_video(file, interview_id, question_id)

    return CommonResponse.success_response("영상 분석 성공", result)

@router.post("/interview/answer/{answer_id}/followup-questions", response_model=FollowupQuestionResponse)
async def generate_followup_questions(
    answer_id: str = Path(..., description="답변 ID")
):
    """
    답변 기반 꼬리 질문 생성 API

    Args:
        answer_id (str): 답변 ID (path parameter)

    Returns:
        FollowupQuestionResponse: 생성된 꼬리 질문들
            - answerId (str): 답변 ID
            - originalAnswer (str): 원본 답변 내용
            - followupQuestions (list): 생성된 꼬리 질문 목록

    Raises:
        HTTPException:
            - 404: 답변을 찾을 수 없음
            - 500: 꼬리 질문 생성 중 오류 발생
    """
    try:
        return await FollowupQuestionService.generate_followup_questions(answer_id)
    except InterviewNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"꼬리 질문 생성 중 오류가 발생했습니다: {str(e)}")
