import os

from app import aws
from app.core.config import settings
from app.repository.answer_repository import AnswerRepository


class S3Service:
    answer_repo = AnswerRepository()

    @staticmethod
    async def upload_to_s3(file_data: bytes, filename: str) -> str:
        s3_key = f"persona/pdfs/{filename}"
        bucket_name = settings.S3_BUCKET_NAME

        aws.client_s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=file_data,
            ContentType="application/pdf"
        )

        url = f"https://{bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
        return url

    @staticmethod
    async def upload_video_file_to_s3(file_path: str, interview_id: str, answer_id: str):
        s3_key = f"interview/{interview_id}/{answer_id}/{os.path.basename(file_path)}"
        bucket_name = settings.S3_BUCKET_NAME

        aws.client_s3.upload_file(
            Filename=file_path,
            Bucket=bucket_name,
            Key=s3_key,
            ExtraArgs={
                "ContentType": "video/webm"
            }
        )
        url = f"s3://{bucket_name}/{s3_key}"
        print(f"✅ S3 업로드 완료: {url}")

        await S3Service.answer_repo.update_answer(answer_id, {"video_url": url})

