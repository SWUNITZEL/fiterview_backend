from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from app.core.database import database
from app.models.question_model import Question

question_collection = database["questions"]

class QuestionRepository:
    def __init__(self):
        self.collection = question_collection

    async def find_by_id(self, id: str) -> Optional[dict]:
        return await self.collection.find_one({"_id": ObjectId(id)})

    async def save_questions(self, interview_id: str, persona: List[str], major: str, university :str, questions: dict[str],
                             comment:str) -> List[str]:
        docs = [
            Question(
                interview_id=interview_id,
                persona=persona,
                major=major,
                university=university,   #프롬프트 정확성 위해 추가
                question_text=q.get("question_text"),
                question_index=int(q.get("question_index")),
                comment=comment,
                total_questions=len(questions),
                created_at=datetime.utcnow()
            ).model_dump()
            for q in questions
        ]
        result = await self.collection.insert_many(docs)
        return [str(_id) for _id in result.inserted_ids]

    async def get_question_by_id(self, question_id: str) -> Optional[dict]:
        try:
            return await self.collection.find_one({"_id": ObjectId(question_id)})
        except Exception:
            return None

    async def get_questions_by_interview_id(self, interview_id: str) -> List[Question]:
        cursor = self.collection.find({"interview_id": interview_id})
        results = []
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            results.append(Question(**doc))
        return results

    async def insert_question(self, question: Question) -> str:
        """
        단일 질문을 DB에 저장하고 생성된 ID 반환
        """
        doc = question.model_dump()
        doc["created_at"] = datetime.utcnow()
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)

    async def update_question(self, question_id: str, question: Question) -> bool:
        """
        기존 질문 업데이트
        """
        doc = question.model_dump()
        doc["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one({"_id": ObjectId(question_id)}, {"$set": doc})
        return result.modified_count > 0


