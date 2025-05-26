import os
import tempfile
from datetime import datetime

from fastapi import UploadFile
from app.core.exceptions.base import AppException
from app.models.interview_model import Interview
from app.repository.interview_repository import InterviewRepository
from app.schemas.response.interview_waiting_room_response import InterviewWaitingRoomResponse
from app.services.land_mark_service import LandmarkService


class InterviewService:
    repo = InterviewRepository()

    @staticmethod
    async def process_landmark(file: UploadFile, combine_id: str) -> InterviewWaitingRoomResponse:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            ear, avg_iris_ratio, smile_point = LandmarkService.calibrate_gaze_points(temp_path)
            if ear is None or avg_iris_ratio is None or smile_point is None:
                raise AppException(status_code=400, message="기준값 추출에 실패했습니다.")

            interview = Interview(
                combine_id=combine_id,
                ear=ear,
                smile_threshold=smile_point,
                avg_iris_ratio=avg_iris_ratio,
                created_at=datetime.utcnow()
            )

            inserted_id = await InterviewService.repo.insert(interview)

            return InterviewWaitingRoomResponse(
                interviewId=inserted_id,
                ear=ear,
                smileThreshold=smile_point,
                avgIrisRatio=avg_iris_ratio
            )
        finally:
            os.remove(temp_path)
