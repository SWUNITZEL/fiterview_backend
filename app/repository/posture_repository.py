from app.core.database import database

calibration_collection = database['posture_calibration']
analysis_collection = database['posture_analysis']

def insert_calibration_data(data: dict):
    return calibration_collection.insert_one(data)

def get_latest_calibration_data():
    return calibration_collection.find_one(sort=[('_id', -1)])

def insert_analysis_data(data: dict):
    return analysis_collection.insert_one(data)

def get_all_analysis_data():
    return list(analysis_collection.find())
