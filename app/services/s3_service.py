import os

import botocore

from app import aws
from app.core.config import settings
from app.core.exceptions.base import AppException
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

        try:
            # S3에 파일 업로드
            aws.client_s3.upload_file(
                Filename=file_path,
                Bucket=bucket_name,
                Key=s3_key,
                ExtraArgs={
                    "ContentType": "video/webm"
                }
            )
            print(f"✅ S3 업로드 완료: s3://{bucket_name}/{s3_key}")
        except botocore.exceptions.BotoCoreError as e:
            print(f"❌ S3 업로드 실패: {e}")
            raise AppException(status_code=500, detail="S3 업로드에 실패했습니다.")
        except Exception as e:
            print(f"❌ 알 수 없는 S3 업로드 오류: {e}")
            raise AppException(status_code=500, detail="S3 업로드 중 예기치 못한 오류가 발생했습니다.")

        # S3 URL 생성
        url = f"s3://{bucket_name}/{s3_key}"

        try:
            # DB에 video_url 업데이트
            answer = await S3Service.answer_repo.update_answer(answer_id, {"video_url": url})

            if not answer:
                print(f"❌ answer_id={answer_id}에 대한 DB 업데이트 실패")
                raise AppException(status_code=404, detail="Answer를 찾을 수 없거나 업데이트에 실패했습니다.")

        except Exception as e:
            print(f"❌ DB 업데이트 중 오류: {e}")
            raise AppException(status_code=500, detail="DB 업데이트 중 오류가 발생했습니다.")

        return answer.video_url

