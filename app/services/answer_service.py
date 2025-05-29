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


        await AnswerService.answer_repo.update_answer(answer_id, {"lexical_analysis": final_result, "endings_analysis": hesitant_endings})
        print("✅ 분석 후 저장 완료")
        return final_result, hesitant_endings

    # 영상에서 표정, 시선처리, 자세 분석 함수
    async def analysis_answer_video(file: UploadFile, interview_id: str, question_id: str) -> AnalysisVideoResponse:
        calibration_data  = await AnswerService.interview_repo.find_all_calibration_data(interview_id)

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

            gaze_down_count = 0
            gaze_down_frame_count = 0
            smiling_frames = 0
            total_frames = 0

            threshold_head = 15
            threshold_shoulder = 20

            head_move_count = 0
            shoulder_move_count = 0
            shoulder_frame_counter = 0
            head_frame_counter = 0

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
                        if ear < calibration_data["ear"] - 0.02:
                            gaze_down_frame_count += 1

                        elif ear > calibration_data["ear"] + 0.02:
                            gaze_down_frame_count = 0

                        # 10프레임 이상 시선이 아래를 향하면 gaze_down_count 추가
                        if (gaze_down_frame_count > 10):
                            gaze_down_count += 1
                            gaze_down_frame_count = 0

                        # 표정 분석
                        smile_score = calculate_smile_points(face_landmarks)

                        if smile_score is not None:
                            if smile_score > calibration_data["smile_threshold"]:
                                smiling_frames += 1
                        else:
                            raise AppException(status_code=400, message="표정 분석 점수 계산에 실패했습니다.") # 계산 실패시 예외 처리

                # 자세 분석
                if pose_results.pose_landmarks:
                    shoulder_distance, head_x = calculate_pose_calibration(pose_results.pose_landmarks, img_h, img_w)

                    # 어깨 움직임 감지 (몸 기울임,가까워 지거나 멀어짐, 위 아래 움직임 모두 고려)
                    if abs(shoulder_distance - calibration_data["shoulder_distance"]) > threshold_shoulder:
                        shoulder_frame_counter += 1
                    else:
                        if shoulder_frame_counter > 5:
                            shoulder_move_count += 1
                        shoulder_frame_counter = 0

                    # 머리 움직임 감지(좌우만)
                    if abs(head_x - calibration_data["head_x"]) > threshold_head:
                        head_frame_counter += 1
                    else:
                        if head_frame_counter > 5:
                            head_move_count += 1
                        head_frame_counter = 0


            cap.release()

            smile_ratio = round(smiling_frames / total_frames, 4)

            return AnalysisVideoResponse(
                interviewId=interview_id,
                answerId=question_id,
                questionId=question_id,
                smileRatio=smile_ratio,
                gazeDownCount=gaze_down_count,
                shoulderMoveCount=shoulder_move_count,
                headMoveCount=head_move_count,
                videoUrl=video_url
            )

        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)



