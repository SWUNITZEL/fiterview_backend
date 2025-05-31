from app.core.database import database
from app.models.user_model import User

user_collection = database['user']


class UserRepository:
    def __init__(self):
        self.collection = user_collection

    async def insert_gaze_analysis_data(self, user: dict):
        return await self.collection.insert_one(user)

    async def find_user(self, email: str) -> User:
        return await self.collection.find_one({"email": email})

