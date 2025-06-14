import os
import shutil
import tempfile

import cv2
from fastapi import UploadFile
from konlpy.tag import Okt
from collections import Counter
import re

from app.analysis.face_mesh_analysis import *
from app.analysis.postureAnalysis import *
from app.core.exceptions.custom import *
from app.repository.answer_repository import *
from app.repository.interview_repository import InterviewRepository
from app.repository.question_repository import QuestionRepository
from app.schemas.response.analysis_video_response import AnalysisVideoResponse
from app.services.s3_service import S3Service


class AnswerService:


    answer_repo = AnswerRepository()
    interview_repo = InterviewRepository()
    question_repo = QuestionRepository()

    # 흐리는 표현 후보
    HESITANT_EXPRESSIONS = [
        '같다', '같은데', '같아요', '같습니다', '듯하다', '듯 합니다', '느낌이에요', '것 같다', '것 같아요'
    ]

    okt = Okt()

    # 답변분석 메서드
    async def analysis_answer( answer_id: str, answer: str):
        # 형태소 분석
        pos_list = AnswerService.extract_pos(answer)
        # 자주 사용된 단어
        word_list = AnswerService.extract_word(pos_list)
        # 말끝을 흐리는 표현
        hesitant_list, score = AnswerService.extract_predicates(pos_list)


        # await AnswerService.answer_repo.update_answer(answer_id,
        #                                               {"lexical_analysis": word_list, "hesitant_list": hesitant_list, "endings_score": score})

        return word_list, hesitant_list, score

    # 형태소 분석
    def extract_pos(text):
        pos = AnswerService.okt.pos(text, stem=True)
        return pos

    # 자주쓰는 단어들 추출
    def extract_word(pos_list):
        words = [(word, pos) for word, pos in pos_list if pos in ['Noun', 'Verb', 'Adjective', 'Determiner']]
        print("주요 품사 단어:", words)

        # 형태소 카운트 (답변 다양성)
        morph_counter = Counter(words).most_common()
        word_list = [(word, count) for (word, pos), count in morph_counter]
        print("답변 다양성:", word_list)

        return word_list

    # 말 끝을 흐리는 어미 추출
    def extract_predicates(pos_list):
        predicates = []
        for i in range(1, len(pos_list)):
            word, tag = pos_list[i]
            prev_word, prev_tag = pos_list[i - 1]

            if tag in ['Verb', 'Adjective']:
                if prev_tag == 'Noun':
                    combined = prev_word + word
                else:
                    combined = word

                # 특수문자 제거
                clean = re.sub(r'^[^\w가-힣]+|[^\w가-힣]+$', '', combined)
                predicates.append(clean)

        # 말끝 흐리는 표현만 필터링
        hesitant = [p for p in predicates if any(p.endswith(h) for h in AnswerService.HESITANT_EXPRESSIONS)]
        counter = Counter(hesitant)
        sorted_hesitant = [word for word, _ in counter.most_common()]

        total = len(predicates)
        hesitant_count = len(hesitant)

        score = int(round(hesitant_count / total, 2) * 100) if total else 0

        return sorted_hesitant, score

    # 영상에서 표정, 시선처리, 자세 분석 함수
    async def analysis_answer_video(file: UploadFile, interview_id: str, question_id: str) -> AnalysisVideoResponse:
        # 인터뷰 존재 여부 확인
        interview = await AnswerService.interview_repo.find_by_id(interview_id)
        if interview is None:
            raise InterviewNotFoundException()

        # 질문 존재 여부 확인
        question = await AnswerService.question_repo.find_by_id(question_id)
        if question is None:
            raise QuestionNotFoundException()

        # 기준 데이터 구하기
        calibration_data  = await AnswerService.interview_repo.find_by_id(interview_id)

        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            temp_file_path = tmp.name
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        # answer 찾기
        answer = await AnswerService.answer_repo.get_by_interview_id_and_question_id(interview_id, question_id)

        # 영상 s3에 업로드
        video_url = await S3Service.upload_video_file_to_s3(temp_file_path, interview_id, answer.id)

        try:
            # 분석 수행
            cap = cv2.VideoCapture(temp_file_path)
            if not cap.isOpened():
                raise InvalidVideoException()

            # face_mesh
            gaze_down_count = 0
            gaze_down_frame_count = 0
            smiling_frames = 0
            total_frames = 0  # 영상 총 프레 수
            fps = cap.get(cv2.CAP_PROP_FPS) # Frame Per Second
            duration_seconds = total_frames / fps # 전체 영상 길이 (초 단위)
            gaze_frame_index = 0
            gaze_sampling_rate = 5
            gaze_points = []
            blink_count = 0
            blink_threshold = 0.21
            eye_closed = False
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

                        else:
                            gaze_down_frame_count = 0

                        # 눈 깜짝임 측정
                        if ear < blink_threshold:
                            if not eye_closed:
                                eye_closed = True
                                blink_count += 1
                        else:
                            eye_closed = False

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

                smile_ratio = round(smiling_frames / total_frames, 4)
                blinks_per_minute = (blink_count / duration_seconds) * 60

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


            # 분석 결과 저장
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

            # 결과 업데이트
            try:
                updated_answer = await S3Service.answer_repo.update_answer(answer.id, update_data)

                if not updated_answer:
                    print(f"❌ answer_id={answer.id}에 대한 DB 업데이트 실패")
                    raise AppException(status_code=404, detail="Answer를 찾을 수 없거나 업데이트에 실패했습니다.")

            except Exception as e:
                print(f"❌ DB 업데이트 중 오류: {e}")
                raise AppException(status_code=500, detail="DB 업데이트 중 오류가 발생했습니다.")

            return AnalysisVideoResponse(
                interviewId=updated_answer.interview_id,
                answerId=str(updated_answer.id),
                questionId=updated_answer.question_id,
                smileRatio=updated_answer.smile_ratio,
                gazeDownCount=updated_answer.gaze_down_count,
                gazePoints=updated_answer.gaze_points,
                blinksPerMinute=blinks_per_minute,
                shoulderTiltCount=updated_answer.shoulder_tilt_count,
                turnLeftCount=updated_answer.turn_left_count,
                turnRightCount=updated_answer.turn_right_count,
                videoUrl=updated_answer.video_url
            )

        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)



