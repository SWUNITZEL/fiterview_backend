import asyncio
import os
import tempfile
import subprocess

from fastapi import WebSocket, WebSocketDisconnect

from app.services.answer_service import AnswerService
from app.services.s3_service import S3Service
from app.services.stt_service import SttService

async def websocket_interview(websocket: WebSocket, interview_id: str):
    await websocket.accept()

    try:
        while True:
            # WebSocket에서 영상 수신
            audio_data = await websocket.receive_bytes()

            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
                temp_file.write(audio_data)
                webm_path = temp_file.name
            try:

                # .wav로 파일 변환
                wav_path = convert_webm_to_wav(webm_path)

                # STT 처리 후 답변 저장
                sentence, answer_id = await SttService().req_upload(wav_path, completion='sync')

                await websocket.send_text(sentence)

                # s3에 영상 저장
                await S3Service.upload_video_file_to_s3(webm_path, interview_id, answer_id)

                # 백그라운드로 답변 분석 및 영상 분석
                asyncio.create_task(AnswerService.analysis_answer(answer_id, sentence))

            finally:
                # 분석 후 파일 삭제
                os.remove(webm_path)
                if os.path.exists(wav_path):
                    os.remove(wav_path)

    except WebSocketDisconnect:
        print("WebSocket 연결 종료")

def convert_webm_to_wav(webm_path: str) -> str:
    wav_path = webm_path.replace('.webm', '.wav')
    command = [
        "ffmpeg",
        "-y",  # 기존 파일 덮어쓰기
        "-i", webm_path,
        "-ar", "16000",       # 샘플링 레이트 16kHz
        "-ac", "1",           # 모노 채널
        "-c:a", "pcm_s16le",  # WAV 기본 인코딩
        wav_path
    ]
    subprocess.run(command, check=True)
    return wav_path