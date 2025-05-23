import os

from app.core.config import settings
import boto3

from app.repository.answer_repository import AnswerRepository


class VideoService:
    repo = AnswerRepository()

    client_s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY
    )

    @staticmethod
    async def upload_to_s3(file_path: str, interview_id: str, answer_id: str):
        s3_key = f"interview/{interview_id}/{answer_id}/{os.path.basename(file_path)}"
        bucket_name = settings.S3_BUCKET_NAME

        VideoService.client_s3.upload_file(
            Filename=file_path,
            Bucket=bucket_name,
            Key=s3_key,
            ExtraArgs={
                "ContentType": "video/webm"
            }
        )
        url = f"s3://{bucket_name}/{s3_key}"
        print(f"✅ S3 업로드 완료: {url}")
        await VideoService.repo.update_answer(answer_id, {"video_url": url})
