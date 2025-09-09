from datetime import datetime
from typing import List, Optional
from pymongo import MongoClient
from bson import ObjectId

from app.core.config import settings
from app.models.question_model import Question


class SyncQuestionRepository:
    def __init__(self):
        client = MongoClient(settings.MONGO_DB_URL)
        self.collection = client[settings.MONGO_DB_NAME]['questions']

    def find_by_id(self, id: str) -> Optional[dict]:
        """ID로 질문 조회"""
        return self.collection.find_one({"_id": ObjectId(id)})

    def save_questions(self, interview_id: str, persona: List[str], major: str, university: str, questions: List[str]) -> List[str]:
        """질문들을 저장하고 삽입된 ID들을 반환"""
        docs = [
            Question(
                interview_id=interview_id,
                persona=persona,
                major=major,
                university=university,
                question_text=q.question_text,
                question_index=q.question_index,
                total_questions=len(questions),
                created_at=datetime.utcnow()
            ).model_dump()
            for q in questions
        ]
        result = self.collection.insert_many(docs)
        return [str(_id) for _id in result.inserted_ids]

    def get_question_by_id(self, question_id: str) -> Optional[dict]:
        """ID로 질문 조회"""
        try:
            return self.collection.find_one({"_id": ObjectId(question_id)})
        except Exception:
            return None

    def get_questions_by_interview_id(self, interview_id: str) -> List[Question]:
        """인터뷰 ID로 질문들 조회"""
        cursor = self.collection.find({"interview_id": interview_id})
        results = []
        for doc in cursor:
            doc["id"] = str(doc["_id"])
            results.append(Question(**doc))
        return results
