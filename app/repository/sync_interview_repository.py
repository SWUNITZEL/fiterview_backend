from typing import Optional
from pymongo import MongoClient
from bson import ObjectId

from app.core.config import settings
from app.models.interview_model import Interview


class SyncInterviewRepository:
    def __init__(self):
        client = MongoClient(settings.MONGO_DB_URL)
        self.collection = client[settings.MONGO_DB_NAME]['interview']

    def insert(self, interview: Interview) -> str:
        """인터뷰를 삽입하고 삽입된 ID를 반환"""
        result = self.collection.insert_one(interview.model_dump())
        return str(result.inserted_id)

    def find_by_id(self, id: str) -> Optional[dict]:
        """ID로 인터뷰 조회"""
        return self.collection.find_one({"_id": ObjectId(id)})

    def update(self, id: str, update_fields: dict) -> bool:
        """인터뷰 업데이트"""
        result = self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_fields, "$currentDate": {"updatedAt": True}}
        )
        return result.modified_count > 0

    def delete(self, id: str) -> bool:
        """인터뷰 삭제"""
        result = self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
