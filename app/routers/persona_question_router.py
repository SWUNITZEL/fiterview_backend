from pathlib import Path

from fastapi import APIRouter, Depends
from numba.scripts.generate_lower_listing import description

from app.core.response import CommonResponse
from app.services.auth_service import AuthService
from app.services.ocr_service import OCRService
from app.services.persona_question_service import PersonaQuestionService

auth_service = AuthService()
router = APIRouter(
    dependencies=[Depends(auth_service.get_current_user)]
)

ocr_service = OCRService()

@router.post("/interview/{interview_id}/persona/question")
async def generate_questions_from_pdf(
    interview_id: str = Path(description="인터뷰 ID")
):
    result = await PersonaQuestionService.createPersonaQuestion(interview_id)

    return CommonResponse.success_response("페르소나 기반 질문 생성 성공", result)


