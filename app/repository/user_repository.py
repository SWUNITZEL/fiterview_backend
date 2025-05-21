from app.core.database import database
from app.models.user_model import User

collection = database['user']

async def insert_gaze_analysis_data(user: dict):
    return await collection.insert_one(user)

async def find_user(email: str) -> User:
    return collection.find_one({"email": email})
