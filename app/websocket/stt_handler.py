from fastapi import WebSocket, WebSocketDisconnect
import grpc
from app.generated import nest_pb2, nest_pb2_grpc

async def websocket_stt(websocket: WebSocket):
    await websocket.accept() # 연결 수락

    # gRPC 채널 설정
    channel = grpc.insecure_channel('localhost:50051')
    stub = nest_pb2_grpc.NestServiceStub(channel)

    def audio_stream_generator(audio_data: bytes):
        yield nest_pb2.AudioChunk(audio_data=audio_data)

    try:
        while True:
            # WebSocket을 통해 음성 데이터 수신
            audio_data = await websocket.receive_bytes()

            # 음성 데이터를 클로바 스피치 API에 전송하고 텍스트로 변환
            response = stub.StreamingRecognize(audio_stream_generator(audio_data))
            # 응답에서 텍스트 추출
            text = response.results[0].alternatives[0].transcript

            # 실시간 음성 인식 결과를 클라이언트로 전송
            await websocket.send_text(f"Recognized: {text}")

    except WebSocketDisconnect:
        print("Client disconnected")