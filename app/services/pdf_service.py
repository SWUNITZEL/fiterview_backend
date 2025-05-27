import os
import boto3
from app.core.config import settings


class PDFService:
    client_s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY
    )

    @staticmethod
    async def upload_to_s3(file_data: bytes, filename: str) -> str:
        s3_key = f"persona/pdfs/{filename}"
        bucket_name = settings.S3_BUCKET_NAME

        PDFService.client_s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=file_data,
            ContentType="application/pdf"
        )

        url = f"https://{bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
        return url
