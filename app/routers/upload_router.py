import os
from typing import List
import tempfile

from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Path

router = APIRouter()

@router.post("/interview/{interviewId}/video/analyze")
async def analyze_videos(interviewId: int, files: List[UploadFile] = File(...)):
    for file in files:
        # 고유한 temp 파일 경로 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # 분석 함수 호출

        # 분석 후 삭제
        os.remove(temp_path)

    return {
        "isSuccess": True,
        "code": "COMMON200",
        "message": "성공입니다.",
        "result": {
            "interviewId": interviewId
        }
    }