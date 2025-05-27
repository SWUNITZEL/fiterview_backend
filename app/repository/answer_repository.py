from bson import ObjectId

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

    async def update_answer(self, answer_id: str, update_data: dict):
        result = await self.collection.update_one(
            {"_id": ObjectId(answer_id)},
            {"$set": update_data}
        )
        return result.modified_count

    async def get_answer_id(self, answer_id: str):
        return await self.collection.find_one({"_id": ObjectId(answer_id)})