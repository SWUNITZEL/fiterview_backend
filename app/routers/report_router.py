from fastapi import APIRouter, HTTPException, Depends, Path
from app.schemas.request.report_request import ReportRequest
from app.schemas.response.report_response import ReportResponse
from app.services.auth_service import AuthService
from app.services.report_service import ReportService
from app.core.exceptions.custom import InterviewNotFoundException


auth_service = AuthService()
report_service = ReportService()
router = APIRouter(dependencies=[Depends(auth_service.get_current_user)])

@router.post("/report/{interview_id}/answer_result", response_model=ReportResponse)
async def generate_report(
    data: ReportRequest,
    interview_id: str = Path(..., description="면접 ID")
):
    """
    면접 결과 보고서를 생성하는 API

    Args:
        data (ReportRequest): 면접 보고서 생성에 필요한 데이터
            - interviewType (str): 면접 유형 ("self_intro" 또는 "essay")
            - questions (list): 질문과 답변 ID 목록
                - questionId (str): 질문 ID
                - answerId (str): 답변 ID
        interview_id (str): 면접 ID (path parameter)

    Returns:
        ReportResponse: 생성된 면접 보고서
            - interviewType (str): 면접 유형
            - report (list): 보고서 내용
                - question (str): 질문 내용
                - intent (str): 질문의 의도
                - answerSummary (str): 답변 요약
                - answerImprovement (str): 답변 개선 제안

    Raises:
        HTTPException:
            - 404: 면접을 찾을 수 없음
            - 500: 보고서 생성 중 오류 발생
    """
    try:
        return await report_service.generate_report(interview_id, data)
    except InterviewNotFoundException:
        raise HTTPException(status_code=404, detail="면접을 찾을 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

