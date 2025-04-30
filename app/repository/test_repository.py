from app.core.database import database

collection = database['test_collection']

async def insert_document(doc: dict):
    return await collection.insert_one(doc)

async def find_document(query: dict):
    return await collection.find_one(query)

async def update_document(id, update_fields):
    return await collection.update_one({"_id": id}, {"$set": update_fields})

async def delete_document(id):
    return await collection.delete_one({"_id": id})