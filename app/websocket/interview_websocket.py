import os
import tempfile
import json
import datetime
import asyncio

from pydub import AudioSegment
from fastapi import WebSocket, WebSocketDisconnect

from app.analysis.voice_anlaysis import calculate_pitch_mean
from app.models.answer_model import Answer
from app.models.question_model import Question
from app.repository.answer_repository import AnswerRepository
from app.repository.question_repository import QuestionRepository
from app.schemas.response.interview_question_response import InterviewQuestionResponse
from app.services.answer_service import AnswerService
from app.services.stt_service import SttService
from app.services.job_manager import job_manager
from app.services.followup_question_service import FollowupQuestionService

question_repo = QuestionRepository()
answer_repo = AnswerRepository()
followup_service = FollowupQuestionService()



async def websocket_interview(websocket: WebSocket, interview_id: str):
    await websocket.accept()

    try:
        # interview_id 기반 질문들 불러오기
        questions = await question_repo.get_questions_by_interview_id(interview_id)
        questions.sort(key=lambda q: q.question_index, reverse=False)

        for question in questions:
            await send_question(websocket, question)

            # 답변 분석
            sentence = await receive_and_process_answer(websocket, interview_id, question.id)

            # 꼬리 질문 생성
            if len(sentence.replace(" ", "")) >= 100:
                followup_question_index = question.question_index + 0.1

                # 꼬리 질문 생성 시도
                for attempt in range(3):  # 최대 3회 재시도
                    try:
                        followup_text = await followup_service.generate_followup_questions(sentence,
                                                                                           question.question_text)
                        followup_question = Question(
                            interview_id=question.interview_id,
                            question_text=followup_text,
                            question_index=followup_question_index,
                            total_questions=question.total_questions,
                            created_at=datetime.datetime.utcnow()
                        )
                        # insert 후 ID 받아오기
                        inserted_question = await question_repo.insert_question(followup_question)
                        followup_question.id = str(inserted_question)

                        await send_question(websocket, followup_question)

                        # 꼬리 질문 답변 분석
                        sentence = await receive_and_process_answer(websocket, interview_id, followup_question.id)
                        break  # 성공 시 재시도 종료
                    except Exception as e:
                        print(f"[WARNING] 꼬리 질문 생성 실패 시도 {attempt + 1}: {e}")
                        if attempt == 2:
                            print("[ERROR] 꼬리 질문 생성 실패, 다음 단계로 진행")
                            break

                # 2차 꼬리 질문 생성
                if len(sentence.replace(" ", "")) >= 100:
                    followup_question_index += 0.1

                    for attempt in range(3):
                        try:
                            followup_text = await followup_service.generate_followup_questions(sentence,
                                                                                               question.question_text)
                            followup_question = Question(
                                interview_id=question.interview_id,
                                question_text=followup_text,
                                question_index=followup_question_index,
                                total_questions=question.total_questions,
                                created_at=datetime.datetime.utcnow()
                            )
                            inserted_question = await question_repo.insert_question(followup_question)
                            followup_question.id = str(inserted_question)

                            await send_question(websocket, followup_question)

                            await receive_and_process_answer(websocket, interview_id, followup_question.id)
                            break
                        except Exception as e:
                            print(f"[WARNING] 2차 꼬리 질문 생성 실패 시도 {attempt + 1}: {e}")
                            if attempt == 2:
                                print("[ERROR] 2차 꼬리 질문 생성 실패, 다음 단계로 진행")
                                break



        # 모든 질문 완료 후 영상 분석 작업 상태 확인 및 응답
        is_completed = await check_video_analysis_completion(websocket, interview_id)

        if is_completed:
            # 종료 멘트
            await websocket.send_text(json.dumps({"question_text": "수고하셨습니다"}))

            # 작업 데이터 정리
            job_manager.cleanup_jobs(interview_id)

    except WebSocketDisconnect:
        print("WebSocket 연결 종료")

# 질문 전송
async def send_question(websocket: WebSocket, question):
    has_followup = True if question.question_index != question.total_questions else False
    type_ = "complete" if not has_followup else "question"
    await websocket.send_text(
        InterviewQuestionResponse(
            questionId=question.id,
            type=type_,
            totalQuestions=question.total_questions,
            questionIndex=question.question_index,
            questionText=question.question_text,
            hasFollowUp=has_followup
        ).json()
    )

# 오디오 수신, STT, 분석, 저장
async def receive_and_process_answer(websocket: WebSocket, interview_id: str, question_id: str) -> str:
    sentence = None
    while sentence is None:
        audio_data = await websocket.receive_bytes()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name

        try:
            sentence = await SttService().req_upload(temp_path, completion='sync')
            if not sentence:
                await websocket.send_text(json.dumps({"question_text": "텍스트를 추출할 수 없습니다."}))
                continue

            word_list, hesitant_list, score = await AnswerService.analysis_answer(sentence)
            speaking_speed = await calculate_speed(sentence, temp_path)
            pitch_mean = await calculate_pitch(temp_path)
            if pitch_mean is None:
                await websocket.send_text("음성 톤 분석 중 오류 발생")

            # 답변 저장
            answer = Answer(
                interview_id=interview_id,
                question_id=question_id,
                answer=sentence,
                speaking_speed=speaking_speed,
                pitch_mean=pitch_mean,
                frequently_used_words=word_list,
                hesitant_list=hesitant_list,
                hesitant_score=score,
                created_at=datetime.datetime.utcnow()
            )
            await answer_repo.insert_document(answer)

            await websocket.send_text(json.dumps({"question_text": "done"}))

        finally:
            os.remove(temp_path)

    return sentence

# 속도 계산
async def calculate_speed(sentence: str, temp_path: str) -> float:
    audio = AudioSegment.from_file(temp_path)
    duration_sec = len(audio) / 1000.0  # ms → sec
    char_count = len(sentence.replace(" ", ""))  # 공백 제외 문자 수
    return char_count / duration_sec if duration_sec > 0 else 0.0

# 평균 톤 계산
async def calculate_pitch(temp_path: str) -> float:
    pitch_mean = calculate_pitch_mean(temp_path)
    return pitch_mean


# 영상 분석 작업 완료 상태를 확인하고 완료 여부를 반환
async def check_video_analysis_completion(websocket: WebSocket, interview_id: str) -> bool:
    try:
        max_wait_time = 300
        check_interval = 5
        elapsed_time = 0

        while elapsed_time < max_wait_time:
            jobs = job_manager.get_interview_jobs(interview_id)

            # 모든 작업이 완료되었는지 확인
            if job_manager.check_all_jobs_completed(interview_id):
                # 모든 작업 완료 시 True 반환
                return True

            await asyncio.sleep(check_interval)
            elapsed_time += check_interval

            # 진행 상황 알림 (30초마다)
            if elapsed_time % 30 == 0:
                jobs = job_manager.get_interview_jobs(interview_id)
                completed_jobs = [job for job in jobs if job["status"] in ["SUCCESS", "FAILURE"]]
                completed_count = len(completed_jobs)
                total_jobs = len(jobs)
                pending_jobs = [job for job in jobs if job["status"] not in ["SUCCESS", "FAILURE"]]
                pending_count = len(pending_jobs)

                await websocket.send_text(json.dumps({
                    "type": "video_analysis_progress",
                    "message": f"영상 분석 진행 중... ({completed_count}/{total_jobs}개 완료)",
                    "pendingJobs": pending_count
                }))

        # 최대 대기 시간 초과
        return False

    except Exception as e:
        print(f"영상 분석 완료 확인 중 오류: {e}")
        # 오류 발생 시 False 반환
        return False
