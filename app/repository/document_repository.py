from typing import Optional

from bson import ObjectId

from app.core.database import database
from app.models.document_model import Document

document_collection = database['documents']

class DocumentRepository:

    def __init__(self):
        self.collection = document_collection


    async def insert_document(self, doc: Document):
        return await self.collection.insert_one(doc.model_dump())

    async def update_document(self, docs_id: str, doc: Document):
        return  await self.collection.update_one(
            {"_id": ObjectId(docs_id)},
            {"$set": doc.model_dump()}
        )

    async def find_by_user_email(self, user_email: str) -> Optional[dict]:
        return await self.collection.find_one({"user_email": user_email})

    async def get_all_documents(self):
        cursor = self.collection.find()
        return await cursor.to_list(length=None)