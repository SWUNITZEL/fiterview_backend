from fastapi import APIRouter, UploadFile, File, HTTPException
from starlette.responses import JSONResponse

from app.services.video_service import save_upload_files, process_video_analysis

router = APIRouter()

UPLOAD_DIR = './uploads/'

@router.post("/upload/")
async def upload_file(video: UploadFile = File(...), img: UploadFile = File(...), q_num: int = 1):
    try:
        await save_upload_files(video, img)
        success, result = await process_video_analysis(q_num)
        if success:
            return JSONResponse(content={"message": "업로드 및 분석 성공", "result": result})
        else:
            return JSONResponse(content={"message": "DB 업데이트 실패", "result": result}, status_code=500)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")