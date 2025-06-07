from fastapi import APIRouter, HTTPException,Depends
from app.schemas.request.report_request import ReportRequest
from app.schemas.response.report_response import ReportResponse
from app.services.auth_service import AuthService
from app.services.report_service import ReportService


auth_service = AuthService()
report_service = ReportService()
router = APIRouter(dependencies=[Depends(auth_service.get_current_user)])

@router.post("/interview/report", response_model=ReportResponse)
async def generate_report(data: ReportRequest):
    """
    면접 결과 보고서 생성 API

    Args:
        data (ReportRequest): 면접 보고서 생성에 필요한 데이터
            - interviewId (str): 면접 ID
            - interviewType (str): 면접 유형 ("self_intro" 또는 "essay")
            - questions (list): 질문과 답변 ID 목록
                - questionId (str): 질문 ID
                - answerId (str): 답변 ID

    Example Request:
        {
            "interviewId": "665f6a5a2b5e2e3b9e8f74d1",
            "interviewType": "self_intro",
            "questions": [
                {
                    "questionId": "665f6a5a2b5e2e3b9e8f74d5",
                    "answerId": "665f6a6b2b5e2e3b9e8f74da"
                },
                {
                    "questionId": "665f6a5a2b5e2e3b9e8f74d6",
                    "answerId": "665f6a6b2b5e2e3b9e8f74db"
                }
            ]
        }

    Returns:
        ReportResponse: 생성된 면접 보고서
            - interviewType (str): 면접 유형
            - report (list): 보고서 내용
                - question (str): 질문 내용
                - intent (str): 질문의 의도
                - answerSummary (str): 답변 요약
                - answerImprovement (str): 답변 개선 (맞춤법)

    Example Response:
        {
            "interviewType": "self_intro",
            "report": [
                {
                    "question": "지원 동기가 무엇인가요?",
                    "intent": "지원자의 전공 선택 이유를 파악하기 위함입니다.",
                    "answerSummary": "수험자는 고등학교 때 수학을 좋아해 통계학에 관심을 갖게 되었습니다.",
                    "answerImprovement": "고등학교에서 수학 동아리를 하며 통계학에 관심을 갖게 되었고, 이에 통계학과를 지원하게 되었습니다."
                }
            ]
        }

    Raises:
        HTTPException: 보고서 생성 중 오류 발생 시 500 에러 반환
    """
    try:
        return await report_service.generate_report(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
