import os
import tempfile
from datetime import datetime
from typing import Dict, Any

import cv2
from celery import current_task

from app.analysis.face_mesh_analysis import *
from app.analysis.postureAnalysis import *
from app.core.exceptions.custom import *
from app.repository.sync_answer_repository import SyncAnswerRepository
from app.repository.sync_interview_repository import SyncInterviewRepository
from app.repository.sync_question_repository import SyncQuestionRepository
from app.services.s3_service import S3Service
from app.services.job_manager import job_manager
from app.core.celery_app import celery_app


def _analyze_video_sync_logic(file_data: bytes, interview_id: str, question_id: str, filename: str) -> Dict[str, Any]:
    """
    영상 분석 동기 로직
    """
    job_id = job_manager.generate_job_id(interview_id, question_id)
    temp_file_path = None

    try:
        job_manager.update_job_status(job_id, "RUNNING")

        # 인터뷰 확인
        interview_repo = SyncInterviewRepository()
        interview = interview_repo.find_by_id(interview_id)
        if interview is None:
            raise InterviewNotFoundException()

        # 질문 확인
        question_repo = SyncQuestionRepository()
        question = question_repo.find_by_id(question_id)
        if question is None:
            raise QuestionNotFoundException()

        # 기준 데이터
        calibration_data = interview_repo.find_by_id(interview_id)
        calibration_dict = (
            calibration_data if isinstance(calibration_data, dict) else
            calibration_data.model_dump() if hasattr(calibration_data, 'model_dump') else calibration_data
        )

        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            temp_file_path = tmp.name
            tmp.write(file_data)

        # 답변 조회
        answer_repo = SyncAnswerRepository()
        answer = answer_repo.get_by_interview_id_and_question_id(interview_id, question_id)
        if answer is None:
            raise AppException(status_code=400, message=f"답변을 찾을 수 없습니다. {interview_id}, {question_id}")

        # 영상 S3 업로드 (업데이트 포함) - S3Service도 동기 방식으로 변경 필요
        video_url = S3Service.upload_video_file_to_s3_sync(temp_file_path, interview_id, str(answer.id))

        # OpenCV로 비디오 분석 (동기적 작업)
        cap = cv2.VideoCapture(temp_file_path)
        if not cap.isOpened():
            raise InvalidVideoException()

        # 초기 변수
        gaze_down_count = gaze_down_frame_count = smiling_frames = total_frames = 0
        gaze_frame_index = 0
        gaze_sampling_rate = 5
        gaze_points = []
        blink_count = 0
        blink_threshold = 0.21
        eye_closed = False

        # pose
        shoulder_tilt_count = turn_left_count = turn_right_count = 0
        prev_label = None
        same_posture_count = 0
        threshold_frame = 10
        sensitivity = 0.02

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            img_h, img_w, _ = frame.shape
            total_frames += 1
            face_mesh_results = face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            pose_results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            # 얼굴 분석
            if face_mesh_results.multi_face_landmarks:
                for face_landmarks in face_mesh_results.multi_face_landmarks:
                    ear, avg_iris_ratio = calculate_gaze_points(face_landmarks, img_h, img_w)

                    gaze_x = int((avg_iris_ratio - calibration_dict["avg_iris_ratio"]) * img_h + img_w / 2)
                    gaze_y = img_h - int((ear - calibration_dict["ear"]) * img_h * 10 + img_w / 2)

                    # 시선 아래
                    if ear < calibration_dict["ear"] * (2 / 3):
                        gaze_down_frame_count += 1
                    else:
                        gaze_down_frame_count = 0

                    # 눈 깜빡임
                    if ear < blink_threshold:
                        if not eye_closed:
                            eye_closed = True
                            blink_count += 1
                    else:
                        eye_closed = False

                    if gaze_down_frame_count > 10:
                        gaze_down_count += 1
                        gaze_down_frame_count = 0

                    # 시선 샘플링
                    if gaze_frame_index % gaze_sampling_rate == 0:
                        saved_gaze_x = min(max(int((gaze_x * 100) / img_w), 0), 100)
                        saved_gaze_y = min(max(int((gaze_y * 100) / img_h), 0), 100)
                        gaze_points.append({
                            "x": saved_gaze_x,
                            "y": saved_gaze_y,
                            "time": datetime.utcnow().isoformat()
                        })

                    smile_score = calculate_smile_points(face_landmarks)
                    if smile_score and smile_score > calibration_dict["smile_threshold"]:
                        smiling_frames += 1

            # 자세 분석
            if pose_results.pose_landmarks:
                shoulder_diff, head_rotation = calculate_pose_calibration(
                    pose_results.pose_landmarks, img_h, img_w)

                posture_label = "GOOD"
                if shoulder_diff > calibration_data["shoulder_diff"] + sensitivity:
                    posture_label = "SHOULDER TILT"
                elif head_rotation > calibration_data["head_rotation"] + sensitivity:
                    posture_label = "TURN RIGHT"
                elif head_rotation < calibration_data["head_rotation"] - sensitivity:
                    posture_label = "TURN LEFT"

                if posture_label == prev_label:
                    same_posture_count += 1
                else:
                    same_posture_count = 1
                    prev_label = posture_label

                if same_posture_count == threshold_frame:
                    if posture_label == "SHOULDER TILT":
                        shoulder_tilt_count += 1
                    elif posture_label == "TURN LEFT":
                        turn_left_count += 1
                    elif posture_label == "TURN RIGHT":
                        turn_right_count += 1
                    same_posture_count = 0

            gaze_frame_index += 1

        cap.release()

        # 최종 계산
        smile_ratio = round(smiling_frames / total_frames, 4) if total_frames > 0 else 0
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        duration_seconds = total_frames / fps
        blinks_per_minute = (blink_count / duration_seconds) * 60 if duration_seconds > 0 else 0

        # DB 업데이트
        update_data = {
            "smile_ratio": smile_ratio,
            "gaze_down_count": gaze_down_count,
            "gaze_points": gaze_points,
            "blinks_per_minute": blinks_per_minute,
            "shoulder_tilt_count": shoulder_tilt_count,
            "turn_left_count": turn_left_count,
            "turn_right_count": turn_right_count,
            "video_url": video_url
        }
        updated_answer = answer_repo.update_answer(str(answer.id), update_data)

        result = updated_answer.model_dump(mode="json")
        job_manager.update_job_status(job_id, "SUCCESS", result)
        return result

    except Exception as e:
        job_manager.update_job_status(job_id, "FAILURE", {"error": str(e)})
        raise e
    finally:
        # 임시 파일 정리
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@celery_app.task(bind=True)
def analyze_video_task(self, file_data: bytes, interview_id: str, question_id: str, filename: str) -> Dict[str, Any]:
    """
    영상 분석을 수행하는 Celery 태스크
    """
    # 동기 로직을 직접 호출
    return _analyze_video_sync_logic(file_data, interview_id, question_id, filename)