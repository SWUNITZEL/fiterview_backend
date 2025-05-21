from app.core.database import database

collection = database['interview']

async def insert_interview(doc: dict):
    result = await collection.insert_one(doc)
    return result.inserted_id  # ObjectId 반환

async def find_interview(query: dict):
    return await collection.find_one(query)

async def update_interview(id, update_fields):
    return await collection.update_one({"_id": id}, {"$set": update_fields})

async def delete_interview(id):
    return await collection.delete_one({"_id": id})