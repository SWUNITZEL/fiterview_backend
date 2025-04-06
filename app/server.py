
import grpc
from app.generated import nest_pb2_grpc, nest_pb2
from motor.motor_asyncio import AsyncIOMotorClient
from collections import Counter
from concurrent import futures
from config.config import settings

# MongoDB 비동기 연결 설정
client = AsyncIOMotorClient(settings.MONGO_DB_URL)
database = client[settings.MONGO_DB_NAME]
reports_collection = database['analysis_reports']
contents_collection = database['report_contents']

class NestService(nest_pb2_grpc.NestServiceServicer):
    async def StreamingRecognize(self, request_iterator, context):
        interview_data = []
        total_words = 0  # 전체 단어 수
        total_duration = 0  # 전체 발화 시간

        # 클로바 스피치 API와의 연결 설정
        channel = grpc.insecure_channel('localhost:50051')
        stub = nest_pb2_grpc.ClovaSpeechStub(channel)

        # API 키 추가
        metadata = [('Authorization', f'Bearer {settings.CLOVA_API_SECRET_KEY}')]

        async for request in request_iterator:
            audio_data = request.audio_data
            # 클로바 스피치 API에 음성을 전송하고 텍스트를 받음
            response = stub.StreamingRecognize(iter([nest_pb2.AudioChunk(audio_data=audio_data)]), metadata=metadata)

            # 음성 인식 결과
            text = response.results[0].alternatives[0].transcript  # 프론트랑 연결 오류나면 수정필요 부분
            start_time = request.start_time
            end_time = request.end_time
            words = text.split()
            duration = end_time - start_time
            words_per_minute = (len(words) / duration) * 60 if duration > 0 else 0

            word_count = Counter(words)
            most_common_words = word_count.most_common(5)

            segment_data = {
                "start_time": start_time,
                "end_time": end_time,
                "text": text,
                "speech_rate": words_per_minute,
                "most_common_words": most_common_words,
                "words_per_minute": words_per_minute,
            }

            interview_data.append(segment_data)

            # MongoDB에 분석 결과 저장 (reports_collection)
            await reports_collection.insert_one({
                "text": text,
                "start_time": start_time,
                "end_time": end_time,
                "speech_rate": words_per_minute,
                "most_common_words": most_common_words,
                "words_per_minute": words_per_minute,
            })

            # MongoDB에 면접 텍스트 내용 저장 (contents_collection)
            await contents_collection.insert_one({
                "text": text,
                "start_time": start_time,
                "end_time": end_time,
            })

            # 실시간 음성 인식 결과를 클라이언트로 전송
            yield nest_pb2.NestResponse(response_message=f"Recognized: {text}")


# gRPC 서버 시작
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    nest_pb2_grpc.add_NestServiceServicer_to_server(NestService(), server)
    server.add_insecure_port('[::]:50051')
    print("Server is running...")
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()

