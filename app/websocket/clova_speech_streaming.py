import os

import grpc
import json

import app.proto.nest_pb2 as nest_pb2
import app.proto.nest_pb2_grpc as nest_pb2_grpc
from app.core.config import settings

AUDIO_PATH = os.path.join(os.getcwd(), "audio", "test_converted.wav")
CLIENT_SECRET = settings.CLOVA_SPEECH_SECRET_KEY

def generate_requests(audio_path):
    # 초기 설정 요청: 음성 인식 설정
    yield nest_pb2.NestRequest(
        type=nest_pb2.RequestType.CONFIG,
        config=nest_pb2.NestConfig(
            config=json.dumps({"transcription": {"language": "ko"}})
        )
    )

    # 오디오 파일을 열고 32,000 바이트씩 읽음
    with open(audio_path, "rb") as audio_file:
        while True:
            chunk = audio_file.read(32000)  # 오디오 파일의 청크를 읽음
            if not chunk:
                break  # 데이터가 더 이상 없으면 루프 종료
            yield nest_pb2.NestRequest(
                type=nest_pb2.RequestType.DATA,
                data=nest_pb2.NestData(
                    chunk=chunk,
                    extra_contents=json.dumps({"seqId": 0, "epFlag": False})
                )
            )

def main():
    # Clova Speech 서버에 대한 보안 gRPC 채널을 설정
    channel = grpc.secure_channel(
        "clovaspeech-gw.ncloud.com:50051",
        grpc.ssl_channel_credentials()
    )

    print("djihsa")
    stub = nest_pb2_grpc.NestServiceStub(channel)  # NestService에 대한 stub 생성
    metadata = (("authorization", f"Bearer {CLIENT_SECRET}"),)  # 인증 토큰과 함께 메타데이터 설정
    responses = stub.recognize(generate_requests(AUDIO_PATH), metadata=metadata)  # 생성된 요청으로 인식(recognize) 메서드 호출

    try:
        # 서버로부터 응답을 반복 처리
        for response in responses:
            print("Received response: " + response.contents)
    except grpc.RpcError as e:
        # gRPC 오류 처리
        print(f"Error: {e.details()}")
    finally:
        channel.close()  # 작업이 끝나면 채널 닫기

if __name__ == "__main__":
    main()
