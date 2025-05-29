import os
import tempfile
from datetime import datetime

from fastapi import UploadFile

from app.analysis.face_mesh_analysis import *
from app.analysis.postureAnalysis import *
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

            face_mesh_results = face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            pose_results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

            if not face_mesh_results.multi_face_landmarks:
                raise AppException(status_code=400, message="얼굴 랜드마크를 찾을 수 없습니다.")

            # face_mesh를 이용한 얼굴 분석 기준점
            face_landmarks = face_mesh_results.multi_face_landmarks[0]
            ear, avg_iris_ratio = calculate_gaze_points(face_landmarks, image.shape[0], image.shape[1])
            smile_point = calculate_smile_points(face_landmarks)

            # pose로 자세 분석 기준점
            pose_landmarks = pose_results.pose_landmarks
            shoulder_distance, head_x = calculate_pose_calibration(pose_landmarks, image.shape[0], image.shape[1])

            interview = Interview(
                combine_id=combine_id,
                ear=ear,
                smile_threshold=smile_point,
                avg_iris_ratio=avg_iris_ratio,
                shoulder_distance=shoulder_distance,
                head_x=head_x,
                created_at=datetime.utcnow()
            )

            new_interview_id = await InterviewService.repo.insert(interview)

            return InterviewWaitingRoomResponse(
                interviewId=new_interview_id,
                ear=ear,
                smileThreshold=smile_point,
                avgIrisRatio=avg_iris_ratio,
                shoulderDistance=shoulder_distance,
                headX=head_x
            )

        finally:
            os.remove(temp_path)