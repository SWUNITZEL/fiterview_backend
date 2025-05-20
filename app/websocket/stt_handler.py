import os
import json
import tempfile

from fastapi import WebSocket, WebSocketDisconnect

from app.services.stt_service import SttService

async def websocket_stt(websocket: WebSocket, intreviewId: int):
    await websocket.accept()

    try:
        while True:
            # WebSocket에서 오디오 수신
            audio_data = await websocket.receive_bytes()

            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name

            try:
                # STT 처리
                result = json.loads(SttService().req_upload(temp_path, completion='sync').text)
                segments = result.get("segments", [])
                if segments:
                    sentence = segments[0].get("text")
                    await websocket.send_text(sentence)
            finally:
                # 분석 후 파일 삭제
                os.remove(temp_path)

    except WebSocketDisconnect:
        print("WebSocket 연결 종료")
