from app.core.database import database
from app.models.combine_model import Combine

combine_collection = database['combine']

class CombineRepository:
    def __init__(self):
        self.collection = combine_collection

    async def insert(self, combine: Combine) -> str:
        result = await self.collection.insert_one(combine.model_dump())
        return str(result.inserted_id)