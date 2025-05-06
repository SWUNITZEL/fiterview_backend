from app.core.database import database

collection = database['calibration_data']

async def insert_calibration_data(calibration_data: dict):
    return await collection.insert_one(calibration_data)

async def get_all_calibration_data():
    cursor = collection.find()
    return await cursor.to_list(length=None)