import os
import json

from fastapi import WebSocket, WebSocketDisconnect

from app.services.stt_service import SttService

SAVE_PATH = os.path.join(os.getcwd(), "received_audio", "audio.wav")

async def websocket_stt(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # WebSocket에서 오디오 수신
            audio_data = await websocket.receive_bytes()

            with open(SAVE_PATH, "wb") as f:
                f.write(audio_data)

            result = json.loads(SttService().req_upload(SAVE_PATH, completion='sync').text)
            segments = result.get("segments", [])
            if segments:
                sentence = segments[0].get("text")
                await websocket.send_text(sentence)

    except WebSocketDisconnect:
        print("WebSocket 연결 종료")
