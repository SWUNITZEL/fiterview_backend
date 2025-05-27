from app.models.feedback_model import Feedback
from app.core.database import database
from datetime import datetime

feedback_collection = database["feedbacks"]

class FeedbackRepository:
    def __init__(self):
        self.collection = feedback_collection

    async def save_feedback(self, feedback: Feedback) -> str:
        if feedback.created_at is None:
            feedback.created_at = datetime.utcnow()

        result = await self.collection.insert_one(feedback.model_dump())
        return str(result.inserted_id)

    async def get_feedback_by_answer_id(self, answer_id: str) -> dict:
        return await self.collection.find_one({"answer_id": answer_id})



