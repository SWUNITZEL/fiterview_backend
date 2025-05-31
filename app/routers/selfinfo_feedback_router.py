from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from datetime import datetime

from app.models.feedback_model import Feedback
from app.repository.answer_repository import AnswerRepository
from app.repository.question_repository import QuestionRepository
from app.repository.selfinfo_feedback_repository import FeedbackRepository
from app.services.auth_service import AuthService
from app.services.selfinfo_feedback_service import build_prompt, generate_feedback

# Repository 인스턴스 생성
answer_repo = AnswerRepository()
question_repo = QuestionRepository()
feedback_repo = FeedbackRepository()


auth_service = AuthService()

router = APIRouter(
    dependencies=[Depends(auth_service.get_current_user)]
)

@router.post("/interview/selfinfo-feedback")
async def improve_answer(payload: Feedback):
    try:
        # 1. 답변 조회
        answer_doc = await answer_repo.get_answer_id(payload.answer_id)
        if not answer_doc or "answer" not in answer_doc:
            raise HTTPException(status_code=404, detail="답변이 존재하지 않음")
        original_answer = answer_doc["answer"]

        # 2. 질문 조회
        question_doc = await question_repo.get_question_by_id(payload.question_id)
        if not question_doc or "question" not in question_doc:
            raise HTTPException(status_code=404, detail="질문이 존재하지 않음")
        question_text = question_doc["question"]

        # 3. 프롬프트 생성 및 GPT 응답
        prompt = build_prompt(question_text, original_answer, payload.major)
        improved_result = generate_feedback(prompt)

        # 4. 모델 업데이트 후 저장
        payload.feedback_text = improved_result
        payload.created_at = datetime.utcnow()
        await feedback_repo.save_feedback(payload)

        return JSONResponse(content={"improved_feedback": improved_result})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


