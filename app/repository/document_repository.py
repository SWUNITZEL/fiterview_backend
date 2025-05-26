from app.core.database import database
from app.models.document_model import Document

document_collection = database['documents']

class DocumentRepository:

    def __init__(self):
        self.collection = document_collection


    async def insert_document(self, doc: Document):
        return await self.collection.insert_one(doc.model_dump())


    async def get_all_documents(self):
        cursor = self.collection.find()
        return await cursor.to_list(length=None)