from app.core.database import database

reports_collection = database["ANALYSIS_REPORTS"]
contents_collection = database["REPORT_CONTENTS"]

async def update_video_analysis(video_json: dict, q_num: int):
    try:
        latest_report = reports_collection.find().sort("rep_idx", -1).limit(1)
        latest = list(latest_report)

        if latest:
            latest_rep_idx = latest[0]['rep_idx']

            # REPORT_CONTENTS 컬렉션에 분석 결과 업데이트
            result = contents_collection.update_one(
                {"rep_idx": latest_rep_idx, "q_num": q_num},
                {"$set": {"video_analysis": video_json}}
            )
            return result.modified_count > 0
        return False
    except Exception as e:
        raise RuntimeError(f"DB update error: {e}")