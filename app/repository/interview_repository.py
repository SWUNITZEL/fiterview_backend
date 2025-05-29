from typing import Optional

from bson import ObjectId

from app.core.database import database
from app.models.interview_model import Interview

interview_collection = database['interview']

class InterviewRepository:
    def __init__(self):
        self.collection = interview_collection

    async def insert(self, interview: Interview) -> str:
        result = await self.collection.insert_one(interview.model_dump())
        return str(result.inserted_id)

    async def find_by_id(self, id: str) -> Optional[dict]:
        return await self.collection.find_one({"_id": ObjectId(id)})

    async def find_smile_threshold_by_id(self, id: str) -> Optional[float]:
        return await self.collection.find_one({"_id": ObjectId(id)}, {"smile_threshold": 1, "_id": 0})

    async def update(self, id: str, update_fields: dict) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_fields, "$currentDate": {"updatedAt": True}}
        )
        return result.modified_count > 0

    async def delete(self, id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0