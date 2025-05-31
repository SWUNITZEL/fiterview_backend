import os
import tempfile
import subprocess

from fastapi import WebSocket, WebSocketDisconnect

from app.models.answer_model import Answer
from app.repository.question_repository import QuestionRepository
from app.schemas.response.interview_question_response import InterviewQuestionResponse
from app.services.stt_service import SttService

repo = QuestionRepository()

async def websocket_interview(websocket: WebSocket, interview_id: str):
    await websocket.accept()

    try:
        # interview_id 기반 질문들 불러오기
        questions = await repo.get_questions_by_interview_id(interview_id)
        questions.sort(key=lambda q: q.question_index, reverse=False)
        print(len(questions))

        for question in questions:
            print(question.question_text)
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

            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            try:
                # STT 처리
                sentence = await SttService().req_upload(temp_path, completion='sync')

                # 답변 저장
                answer = Answer(
                    interview_id=interview_id,
                    question_id=question.question_id,
                    answer=sentence
                )
                await SttService.repo.insert_document(answer)

                print(sentence)
            finally:
                # 파일 삭제
                os.remove(temp_path)

    except WebSocketDisconnect:
        print("WebSocket 연결 종료")