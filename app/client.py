import grpc
import asyncio
from websockets import connect
from app.generated import nest_pb2_grpc, nest_pb2

# gRPC 클라이언트 설정
def create_grpc_channel():
    channel = grpc.insecure_channel('localhost:50051')  # gRPC 서버 주소
    stub = nest_pb2_grpc.NestServiceStub(channel)
    return stub

# WebSocket을 통해 실시간으로 음성 데이터를 보내는 클라이언트
async def send_audio_data():
    async with connect("ws://localhost:8000/stt/ws") as websocket:
        stub = create_grpc_channel()

        # 음성 파일을 청크 단위로 읽고 WebSocket을 통해 서버로 전송
        with open("audio.wav", "rb") as f:
            while True:
                chunk = f.read(32000)  #clova speech api 최적크기
                if not chunk:
                    break

                # WebSocket을 통해 서버로 음성 데이터 전송
                await websocket.send(chunk)

                # gRPC를 통해 서버로 음성 데이터를 보내고 텍스트 결과를 받음
                responses = stub.StreamingRecognize(generate_audio_requests(chunk))

                # 서버로부터 실시간 음성 인식 결과를 받음
                for response in responses:
                    print("Received response from gRPC:", response.response_message)

                # 실시간 음성 인식 결과를 WebSocket 클라이언트로 전송
                result = await websocket.recv()
                print("Recognized: ", result)

# 음성 데이터를 gRPC 요청에 맞는 형식으로 변환
def generate_audio_requests(audio_data):
    # 오디오 데이터를 NestRequest에 맞게 변환 (프론트 연결 오류나면 수정필요)
    yield nest_pb2.NestRequest(
        type=nest_pb2.RequestType.DATA,
        data=nest_pb2.NestData(
            chunk=audio_data,
            extra_contents="{}"
        )
    )

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(send_audio_data())
