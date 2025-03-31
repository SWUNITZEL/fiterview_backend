from fastapi import APIRouter, UploadFile, File
import os
import uuid
from app.services.stt_service import transcribe_wav

router = APIRouter(prefix="/stt", tags=["STT"])

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/")
async def stt_endpoint(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.wav")

    with open(file_path, "wb") as f:
        f.write(await file.read())

    try:
        text = transcribe_wav(file_path)
        return {"text": text}
    finally:
        os.remove(file_path)
