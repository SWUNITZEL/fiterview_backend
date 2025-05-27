from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from app.core.database import database
from app.models.question_model import Question

question_collection = database["questions"]

class QuestionRepository:
    def __init__(self):
        self.collection = question_collection

    async def save_questions(self, persona: str, major: str, questions: List[str]) -> List[str]:
        docs = [
            Question(
                persona=persona,
                major=major,
                question=q,
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


