from app.core.database import database

collection = database['gaze_analysis_data']

async def insert_gaze_analysis_data(gaze_analysis_data: dict):
    return await collection.insert_one(gaze_analysis_data)

async def get_all_gaze_analysis_data():
    cursor = collection.find()
    return await cursor.to_list(length=None)