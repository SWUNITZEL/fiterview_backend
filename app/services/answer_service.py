import os
import shutil
import tempfile

import cv2
from fastapi import UploadFile
from konlpy.tag import Mecab
import mediapipe as mp
from collections import Counter

from app.analysis.facial_analysis import *
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
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1,
                                          refine_landmarks=True,
                                          min_detection_confidence=0.6,
                                          min_tracking_confidence=0.7)
        detect_smile_threshold = await AnswerService.interview_repo.find_smile_threshold_by_id(interview_id)

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

            smiling_frames = 0
            total_frames = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                total_frames += 1
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(frame_rgb)

                if results.multi_face_landmarks:
                    for face_landmarks in results.multi_face_landmarks:
                        img_h, img_w, _ = frame.shape

                        smile_score = calculate_smile_points(face_landmarks)

                        if smile_score is not None:
                            if smile_score > detect_smile_threshold["smile_threshold"]:
                                smiling_frames += 1
                        else:
                            raise SmileAnalysisException() # 계산 실패시 예외 처리

            cap.release()

            if total_frames == 0:
                return {"smile_ratio": 0.0, "smiling_frames": 0, "total_frames": 0}

            smile_ratio = round(smiling_frames / total_frames, 4)

            return AnalysisVideoResponse(
                interviewId=interview_id,
                answerId=question_id,
                questionId=question_id,
                smileRatio=smile_ratio,
                videoUrl=video_url
            )

        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)



