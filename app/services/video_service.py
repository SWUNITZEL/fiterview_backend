import os
from app.repository.video_repository import update_video_analysis
from app import analysis

UPLOAD_DIR = './uploads/'

async def save_upload_files(video, img):
    video_path = os.path.join(UPLOAD_DIR, video.filename)
    img_path = os.path.join(UPLOAD_DIR, img.filename)

    with open(video_path, "wb") as vf:
        vf.write(await video.read())
    with open(img_path, "wb") as imf:
        imf.write(await img.read())

    return video_path, img_path


async def process_video_analysis(q_num: int):
    result_json = analysis()
    update_success = await update_video_analysis(result_json, q_num)
    return update_success, result_json