from typing import Optional

from bson import ObjectId
from pymongo import ReturnDocument

from app.core.database import database
from app.models.answer_model import Answer

answer_collection = database['answers']

class AnswerRepository:
    def __init__(self):
        self.collection = answer_collection

    async def insert_document(self, answer: Answer):
        result = await self.collection.insert_one(answer.model_dump())
        return str(result.inserted_id)

    async def get_all_answers(self):
        cursor = self.collection.find()
        return await cursor.to_list(length=None)

    async def update_answer(self, answer_id: str, update_data: dict) -> Optional[Answer]:
        updated_doc = await self.collection.find_one_and_update(
            {"_id": ObjectId(answer_id)},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )
        return Answer(**updated_doc)

    async def get_answer_id(self, answer_id: str):
        return await self.collection.find_one({"_id": ObjectId(answer_id)})

    async def get_by_interview_id_and_question_id(self, interview_id: str, question_id: str) -> Optional[Answer]:
        doc = await self.collection.find_one({
            "interview_id": interview_id,
            "question_id": question_id
        })
        if doc:
            doc["id"] = str(doc["_id"])
            return Answer(**doc)
        return None