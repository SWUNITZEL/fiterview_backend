from typing import Optional
from pymongo import MongoClient
from pymongo import ReturnDocument
from bson import ObjectId

from app.core.config import settings
from app.models.answer_model import Answer


class SyncAnswerRepository:
    def __init__(self):
        client = MongoClient(settings.MONGO_DB_URL)
        self.collection = client[settings.MONGO_DB_NAME]['answers']

    def insert_document(self, answer: Answer) -> str:
        """답변 문서를 삽입하고 삽입된 ID를 반환"""
        result = self.collection.insert_one(answer.model_dump())
        return str(result.inserted_id)

    def get_all_answers(self) -> list:
        """모든 답변을 조회"""
        cursor = self.collection.find()
        return list(cursor)

    def update_answer(self, answer_id: str, update_data: dict) -> Optional[Answer]:
        """답변을 업데이트하고 업데이트된 문서를 반환"""
        updated_doc = self.collection.find_one_and_update(
            {"_id": ObjectId(answer_id)},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )
        if updated_doc:
            return Answer(**updated_doc)
        return None

    def get_answer_id(self, answer_id: str) -> Optional[dict]:
        """ID로 답변 조회"""
        return self.collection.find_one({"_id": ObjectId(answer_id)})

    def get_by_interview_id_and_question_id(self, interview_id: str, question_id: str) -> Optional[Answer]:
        """인터뷰 ID와 질문 ID로 답변 조회"""
        doc = self.collection.find_one({
            "interview_id": interview_id,
            "question_id": question_id
        })
        if doc:
            return Answer(**doc)
        return None
