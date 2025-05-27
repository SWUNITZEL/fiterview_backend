from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.ocr_service import OCRService
from app.services.persona_question_service import generate_interview_questions
from app.services.pdf_service import PDFService
from app.repository.question_repository import QuestionRepository

router = APIRouter()
question_repo = QuestionRepository()
ocr_service = OCRService()

@router.post("/interview/persona/question")
async def generate_questions_from_pdf(
        file: UploadFile = File(...),
        persona_label: str = Form(...),
        major: str = Form(...)
):
    try:
        # 파일 읽기
        content = await file.read()

        # S3 업로드
        s3_url = await PDFService.upload_to_s3(content, file.filename)

        # OCR 처리
        ocr_result = await ocr_service.process_pdf_ocr(content)
        document_text = "\n".join(item["text"] for item in ocr_result if item.get("text", "").strip())

        if not document_text.strip():
            raise HTTPException(status_code=400, detail="문서에서 텍스트를 추출할 수 없습니다.")

        # 질문 생성
        questions = await generate_interview_questions(document_text, persona_label, major)

        # MongoDB에 저장
        question_ids = await question_repo.save_questions(
            persona=persona_label,
            major=major,
            questions=questions
        )

        return {
            "persona_label": persona_label,
            "major": major,
            "questions": questions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


