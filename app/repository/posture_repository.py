from app.core.database import database

calibration_collection = database['posture_calibration']
analysis_collection = database['posture_analysis']

async def insert_calibration_data(data: dict):
    return await calibration_collection.insert_one(data)

async def get_latest_calibration_data():
    return await calibration_collection.find_one(sort=[('_id', -1)])

async def insert_analysis_data(data: dict):
    return await analysis_collection.insert_one(data)

async def get_all_analysis_data():
    cursor = analysis_collection.find()
    return await cursor.to_list(length=None)
