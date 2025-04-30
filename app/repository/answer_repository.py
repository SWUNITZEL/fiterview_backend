from app.core.database import database

collection = database['answers']

async def insert_document(doc: dict):
    return await collection.insert_one(doc)

async def get_all_answers():
    cursor = collection.find()
    return await cursor.to_list(length=None)