import os
import tempfile
from datetime import datetime

import cv2
from fastapi import UploadFile

from app.analysis.face_mesh_analysis import *
from app.core.exceptions.custom import *
from app.models.interview_model import Interview
from app.repository.interview_repository import InterviewRepository
from app.schemas.response.interview_waiting_room_response import InterviewWaitingRoomResponse


class InterviewService:
    repo = InterviewRepository()

    @staticmethod
    async def process_landmark(file: UploadFile, combine_id: str) -> InterviewWaitingRoomResponse:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            image = cv2.imread(temp_path)
            if image is None:
                raise ImageNotFoundException()

            results = face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

            if not results.multi_face_landmarks:
                raise AppException(status_code=400, message="얼굴 랜드마크를 찾을 수 없습니다.")

            face_landmarks = results.multi_face_landmarks[0]
            ear, avg_iris_ratio = calculate_gaze_points(face_landmarks, image.shape[0], image.shape[1])
            smile_point = calculate_smile_points(face_landmarks)

            if ear is None or avg_iris_ratio is None or smile_point is None:
                raise AppException(status_code=400, message="기준값 추출에 실패했습니다.")

            interview = Interview(
                combine_id=combine_id,
                ear=ear,
                smile_threshold=smile_point,
                avg_iris_ratio=avg_iris_ratio,
                created_at=datetime.utcnow()
            )

            new_interview_id = await InterviewService.repo.insert(interview)

            return InterviewWaitingRoomResponse(
                interviewId=new_interview_id,
                ear=ear,
                smileThreshold=smile_point,
                avgIrisRatio=avg_iris_ratio
            )

        finally:
            os.remove(temp_path)