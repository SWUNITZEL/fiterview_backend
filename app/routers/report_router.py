from fastapi import APIRouter, HTTPException, Depends, Path
from app.schemas.response.report_response import ReportResponse
from app.services.auth_service import AuthService
from app.services.report_service import ReportService
from app.core.exceptions.custom import InterviewNotFoundException

auth_service = AuthService()
report_service = ReportService()
router = APIRouter(dependencies=[Depends(auth_service.get_current_user)])

@router.post("/report/{interview_id}/answer_result", response_model=ReportResponse)
async def generate_report(
    interview_id: str = Path(..., description="면접 ID")
):
    """
    면접 결과 보고서를 생성하는 API

    Args:
        interview_id (str): 면접 ID (path parameter)

    Returns:
        ReportResponse: 생성된 면접 보고서
            - report (List[QuestionReport]): 보고서 항목 리스트
                - question (str): 질문 내용
                - intent (str): 질문 의도
                - answerText (str): 원본 답변
                - evaluation (List[str]): 평가 항목 제목 리스트
                - goodExample (str): 개선된 모범답변 예시
                - summary (str): 답변 요약

    Raises:
        HTTPException:
            - 404: 면접을 찾을 수 없음
            - 500: 보고서 생성 중 오류 발생
    """
    try:
        return await report_service.generate_report(interview_id)
    except InterviewNotFoundException:
        raise HTTPException(status_code=404, detail="면접을 찾을 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"보고서 생성 중 오류: {str(e)}")

