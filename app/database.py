from motor.motor_asyncio import AsyncIOMotorClient
from .config.config import settings


# MongoDB 연결 설정
client = AsyncIOMotorClient(settings.MONGO_DB_URL,
    tls=True,  # SSL 연결 사용
    tlsAllowInvalidCertificates=True  )
database = client[settings.MONGO_DB_NAME]

# 컬렉션 가져오기
reports_collection = database['analysis_reports']
contents_collection = database['report_contents']
documents_collection = database['documents']

# 문서 삽입
async def insert_document(collection, document):
    await collection.insert_one(document)

# 문서 검색
async def find_document(collection, query):
    document = await collection.find_one(query)
    return document


async def update_video_analysis(video_json, q_num):
    try:

        latest_report = reports_collection.find().sort("rep_idx", -1).limit(1)

        if latest_report.count_documents({}) > 0:  # count_documents() 사용
            latest_rep_idx = latest_report[0]['rep_idx']

            # REPORT_CONTENTS 컬렉션에 분석 결과 업데이트
            update_result = contents_collection.update_one(
                {'rep_idx': latest_rep_idx, 'q_num': q_num},  # 조건: rep_idx와 q_num
                {'$set': {'video_analysis': video_json}}  # 업데이트할 내용
            )

            if update_result.modified_count > 0:
                print(f"rep_idx가 {latest_rep_idx}인 ANALYSIS_REPORTS 컬렉션에 답변 비디오 분석 결과 업데이트 성공")
            else:
                print(f"rep_idx가 {latest_rep_idx}인 REPORT_CONTENTS 컬렉션에 분석 결과 업데이트 실패")
        else:
            print("가장 최근의 rep_idx를 찾을 수 없습니다.")

    except Exception as e:
        print("Error while connecting to MongoDB", e)

    finally:
        print("DB 접속 종료")



# 테스트용 실행 코드 (비동기 함수 내부에서 await 사용)
async def main():
    video_json = {
        "hand_state": "Hand Raised",
        "emotion": "Neutral"
    }
    q_num = 1

    # 여기서 await 사용
    await update_video_analysis(video_json, q_num)

# DB 작업 후 연결 종료
async def close_connection():
    client.close()
    print("MongoDB 접속 종료")

