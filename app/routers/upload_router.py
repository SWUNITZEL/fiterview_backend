import os
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Request

router = APIRouter()

SAVE_PATH = os.path.join(os.getcwd(), "received_video")

@router.post("/analyze/videos")
async def analyze_videos(request: Request):
    body = await request.body()
    print(f"요청 본문 크기: {len(body)} 바이트")

    form = await request.form()
    files: List[UploadFile] = []

    # FormData에 포함된 모든 항목 중 UploadFile인 것만 추출
    for key, value in form.items():
        if isinstance(value, UploadFile):
            files.append(value)

    analysis_results = []

    for file in files:
        # 영상 저장
        file_path = os.path.join(SAVE_PATH, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        print(f"저장 완료: {file_path}")
        # 분석 (여기서 MediaPipe 분석 함수 호출)

        # 저장 파일 삭제 (분석 후 삭제를 원할 경우 주석 해제)
        # os.remove(file_path)

    return {"results": analysis_results}