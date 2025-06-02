from typing import Annotated

from fastapi import APIRouter, UploadFile, File, Depends

from app.core.response import CommonResponse
from app.models.user_model import User
from app.schemas.response.document_response import DocumentResponse
from app.services.document_service import DocumentService
from app.services.auth_service import AuthService

router = APIRouter()
document_service = DocumentService()
auth_service = AuthService()

@router.post("/school-records/upload",  response_model=CommonResponse[DocumentResponse],)
async def upload_document(
        current_user: Annotated[User, Depends(auth_service.get_current_user)],
        file: UploadFile = File(...),
):
    document_response = await document_service.process_document(file, current_user.get("email"))
    # document_response = await document_service.test(current_user.get("email"))

    return CommonResponse.success_response("생활기록부 업로드 성공", document_response)
