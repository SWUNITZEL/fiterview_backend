from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.response import CommonResponse
from app.services.document_service import DocumentService

router = APIRouter()
document_service = DocumentService()

@router.post("/school-records/upload")
async def upload_document(file: UploadFile = File(...)):
    document_response = await document_service.process_document(file)

    return CommonResponse.success_response("생활기록부 업로드 성공", document_response)
