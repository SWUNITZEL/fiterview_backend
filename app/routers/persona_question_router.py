from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from app.services.auth_service import AuthService
from app.services.ocr_service import OCRService
from app.services.persona_question_service import PersonaQuestionService
from app.repository.question_repository import QuestionRepository
from app.services.s3_service import S3Service

auth_service = AuthService()
router = APIRouter(
    dependencies=[Depends(auth_service.get_current_user)]
)

question_repo = QuestionRepository()
ocr_service = OCRService()

@router.post("/interview/persona/question")
async def generate_questions_from_pdf(
    file: UploadFile = File(...),
    persona_label: str = Form(...),
    major: str = Form(...),
    interview_id: str = Form(...)
):
    try:
        # 파일 읽기
        content = await file.read()

        # S3 업로드
        s3_url = await S3Service.upload_to_s3(content, file.filename)

        # OCR 처리
        ocr_result = await ocr_service.process_pdf_ocr(content)
        document_text = "\n".join(item["text"] for item in ocr_result if item.get("text", "").strip())

        if not document_text.strip():
            raise HTTPException(status_code=400, detail="문서에서 텍스트를 추출할 수 없습니다.")

        # 질문 + 꼬리질문 생성
        questions = await PersonaQuestionService.generate_interview_questions(
            document_text=document_text,
            persona_label=persona_label,
            major=major,
            interview_id=interview_id
        )

        # MongoDB에 저장
        question_ids = await question_repo.save_questions(
            persona=persona_label,
            major=major,
            questions=questions
        )

        return {
            "personaLabel": persona_label,
            "major": major,
            "questions": questions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


