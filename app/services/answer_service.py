import os
import shutil
import tempfile

import cv2
from fastapi import UploadFile
from konlpy.tag import Mecab
from collections import Counter

from app.analysis.face_mesh_analysis import *
from app.analysis.postureAnalysis import *
from app.core.exceptions.custom import *
from app.repository.answer_repository import *
from app.repository.interview_repository import InterviewRepository
from app.schemas.response.analysis_video_response import AnalysisVideoResponse
from app.services.s3_service import S3Service


class AnswerService:
    answer_repo = AnswerRepository()
    interview_repo = InterviewRepository()


    # 어미 분석, 어휘 다양성 분석 서비스 함수
    async def analysis_answer(answer_id: str, answer: str) :
        m = Mecab()

        # Mecab의 전체 품사 태깅 결과 확인
        pos_list = m.pos(answer)

        # 형태소 분석: 명사, 동사, 형용사 등 주요 품사 추출
        words = [(word, pos) for word, pos in m.pos(answer) if
                 pos.startswith('N') or pos.startswith('V') or pos.startswith('MM')]

        # 답변 다양성
        morph_counter = Counter(words).most_common()
        final_result = [(word, count) for (word, pos), count in morph_counter]

        # 서술어 추출
        predicates = []

        for i in range(1, len(pos_list)):
            if "EF" in pos_list[i][1]:
                if pos_list[i - 1][1].startswith("N"):
                    predicates.append(pos_list[i][0])

                else:
                    predicates.append(pos_list[i - 1][0] + pos_list[i][0])


        hesitant_endings = [word for word in predicates if word in ['같은데', '같아요', '같습니다', '듯 합니다', '느낌이에요']]


        # await AnswerService.answer_repo.update_answer(answer_id, {"lexical_analysis": final_result, "endings_analysis": hesitant_endings})
        print("✅ 분석 후 저장 완료")
        return final_result, hesitant_endings

    # 영상에서 표정, 시선처리, 자세 분석 함수
    async def analysis_answer_video(file: UploadFile, interview_id: str, question_id: str) -> AnalysisVideoResponse:
        # 인터뷰 존재 여부 확인
        interview = await AnswerService.interview_repo.find_by_id(interview_id)
        if interview is None:
            raise InterviewNotFoundException();

        calibration_data  = await AnswerService.interview_repo.find_by_id(interview_id)

        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            temp_file_path = tmp.name
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        # 영상 s3에 업로드
        video_url = await S3Service.upload_video_file_to_s3(temp_file_path, interview_id, "sdsda") # answer_id 수정 필요

        try:
            # 분석 수행
            cap = cv2.VideoCapture(temp_file_path)
            if not cap.isOpened():
                raise InvalidVideoException()

            # face_mesh
            gaze_down_count = 0
            gaze_down_frame_count = 0
            smiling_frames = 0
            total_frames = 0
            gaze_frame_index = 0
            gaze_sampling_rate = 5
            gaze_points = []
            saved_gaze_x = 0
            saved_gaze_y = 0

            # pose
            shoulder_tilt_count = 0
            turn_left_count = 0
            turn_right_count = 0
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

                        # 시선 분석
                        ear, avg_iris_ratio = calculate_gaze_points(face_landmarks, img_h, img_w)

                        gaze_x = int((avg_iris_ratio - calibration_data["avg_iris_ratio"]) * img_h + img_w / 2)
                        gaze_y = img_h - int((ear - calibration_data["ear"]) * img_h * 10 + img_w / 2)

                        # 시선이 아래로 향하면 카운터에 1 추가
                        if ear < calibration_data["ear"] * (2/3):
                            gaze_down_frame_count += 1

                        else :
                            gaze_down_frame_count = 0

                        # 10프레임 이상 시선이 아래를 향하면 gaze_down_count 추가
                        if (gaze_down_frame_count > 10):
                            gaze_down_count += 1
                            gaze_down_frame_count = 0

                        # 5프레임당 한 번 시선 정보 저장
                        if gaze_frame_index % gaze_sampling_rate == 0:
                            saved_gaze_x = 0
                            saved_gaze_y = 0
                            # X 좌표 정규화
                            if 0 < gaze_x < img_w:
                                saved_gaze_x = int((gaze_x * 100) / img_w)
                            elif gaze_x <= 0:
                                saved_gaze_x = 0
                            elif gaze_x >= img_w:
                                saved_gaze_x = 100

                            # Y 좌표 정규화
                            if 0 < gaze_y < img_h:
                                saved_gaze_y = int((gaze_y * 100) / img_h)
                            elif gaze_y <= 0:
                                saved_gaze_y = 0
                            elif gaze_y >= img_h:
                                saved_gaze_y = 100
                            gaze_points.append((saved_gaze_x, saved_gaze_y))

                        # 표정 분석
                        smile_score = calculate_smile_points(face_landmarks)

                        if smile_score is not None:
                            if smile_score > calibration_data["smile_threshold"]:
                                smiling_frames += 1
                        else:
                            raise AppException(status_code=400, message="표정 분석 점수 계산에 실패했습니다.") # 계산 실패시 예외 처리

                # 자세 분석
                if pose_results.pose_landmarks:
                    shoulder_diff, head_rotation = calculate_pose_calibration(pose_results.pose_landmarks, img_h, img_w)

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

            cap.release()

            smile_ratio = round(smiling_frames / total_frames, 4)

            return AnalysisVideoResponse(
                interviewId=interview_id,
                answerId=question_id,
                questionId=question_id,
                smileRatio=smile_ratio,
                gazeDownCount=gaze_down_count,
                gazePoints=gaze_points,
                shoulderTiltCount=shoulder_tilt_count,
                turnLeftCount=turn_left_count,
                turnRightCount=turn_right_count,
                videoUrl=video_url
            )

        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)



