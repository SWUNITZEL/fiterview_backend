from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# 로컬 테스트용
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["interview_db"]

# 질문 저장
async def save_questions_to_mongo(persona: str, major: str, questions: list):
    docs = [{
        "persona": persona,
        "major": major,
        "question": q,
        "created_at": datetime.utcnow()
    } for q in questions]

    result = await db["questions"].insert_many(docs)
    return [str(_id) for _id in result.inserted_ids]

# 피드백 저장
async def save_feedback_to_mongo(
    question_id: str,
    answer_id: str,
    major: str,
    feedback_text: str
) -> str:
    doc = {
        "question_id": question_id,
        "answer_id": answer_id,
        "major": major,
        "feedback_text": feedback_text,
        "created_at": datetime.utcnow()
    }
    result = await db["feedbacks"].insert_one(doc)
    return str(result.inserted_id)
