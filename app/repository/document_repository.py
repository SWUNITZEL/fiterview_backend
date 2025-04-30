from app.core.database import database

collection = database['documents']

async def insert_document(doc: dict):
    return await collection.insert_one(doc)

async def get_all_documents():
    cursor = collection.find()
    return await cursor.to_list(length=None)