import os
import tempfile
import json
import datetime

from pydub import AudioSegment
from fastapi import WebSocket, WebSocketDisconnect

from app.analysis.voice_anlaysis import calculate_pitch_mean
from app.models.answer_model import Answer
from app.repository.answer_repository import AnswerRepository
from app.repository.question_repository import QuestionRepository
from app.schemas.response.interview_question_response import InterviewQuestionResponse
from app.services.answer_service import AnswerService
from app.services.stt_service import SttService

repo = QuestionRepository()
answer_repo = AnswerRepository()

async def websocket_interview(websocket: WebSocket, interview_id: str):
    await websocket.accept()

    try:
        # interview_id 기반 질문들 불러오기
        questions = await repo.get_questions_by_interview_id(interview_id)
        questions.sort(key=lambda q: q.question_index, reverse=False)

        for question in questions:
            # 질문 전송
            if question.question_index == question.total_questions:
                await websocket.send_text(
                    InterviewQuestionResponse(
                        questionId=question.id,
                        type="complete",
                        totalQuestions=question.total_questions,
                        questionIndex=question.question_index,
                        questionText=question.question_text,
                        hasFollowUp=False
                    ).json())
            else:
                await websocket.send_text(
                    InterviewQuestionResponse(
                        questionId=question.id,
                        type="question",
                        totalQuestions=question.total_questions,
                        questionIndex=question.question_index,
                        questionText=question.question_text,
                        hasFollowUp=True
                    ).json())

            # 오디오 수신
            audio_data = await websocket.receive_bytes()

            # 꼬리 질문 생성
                # 질문 생성 후 db 저장
                # questions 질문 리스트에 질문 모델 추가.

            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            try:
                # STT 처리
                sentence = await SttService().req_upload(temp_path, completion='sync')
                if sentence is None:
                    print("텍스트를 추출할 수 없습니다.")
                    websocket.send_text("텍스트를 추출할 수 없습니다.")

                word_list, hesitant_list, score = await AnswerService.analysis_answer(sentence)

                # 속도 계산
                audio = AudioSegment.from_file(temp_path)
                duration_sec = len(audio) / 1000.0  # ms → sec

                char_count = len(sentence.replace(" ", ""))  # 공백 제외 문자 수
                if duration_sec > 0:
                    speaking_speed = char_count / duration_sec  # 문자/초
                else:
                    speaking_speed = 0

                # 평균 톤 계산
                pitch_mean = calculate_pitch_mean(temp_path)
                if pitch_mean is None:
                    websocket.send_text("톤 계산 중 오류 발생")

                # 답변 저장
                answer = Answer(
                    interview_id = interview_id,
                    question_id = question.id,
                    answer = sentence,
                    speaking_speed = speaking_speed,
                    pitch_mean = pitch_mean,
                    frequently_used_words=word_list,
                    hesitant_list = hesitant_list,
                    hesitant_score=score,
                    created_at=datetime.datetime.utcnow()
                )
                await answer_repo.insert_document(answer)

                await websocket.send_text(json.dumps({"question_text": "done"}))
            finally:
                # 파일 삭제
                os.remove(temp_path)

        # 종료 멘트
        await websocket.send_text(json.dumps({"question_text": "수고하셨습니다"}))

    except WebSocketDisconnect:
        print("WebSocket 연결 종료")