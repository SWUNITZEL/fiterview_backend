# app/aws.py
import os
from functools import lru_cache
import boto3
from app.core.config import settings


def _resolve_region() -> str:
    return (
        getattr(settings, "AWS_DEFAULT_REGION", None)
        or getattr(settings, "AWS_REGION", None)
        or os.getenv("AWS_DEFAULT_REGION")
        or os.getenv("AWS_REGION")
        or "ap-northeast-2"
    )


@lru_cache(maxsize=1)
def get_s3_client():
    """
    표준 AWS 환경변수만 사용:
      - AWS_ACCESS_KEY_ID
      - AWS_SECRET_ACCESS_KEY
      - AWS_DEFAULT_REGION / AWS_REGION
    값이 없으면 boto3의 기본 자격 증명 체인(IAM Role 등)을 사용.
    """
    access_key = os.getenv("AWS_ACCESS_KEY_ID") or getattr(settings, "AWS_ACCESS_KEY_ID", None)
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY") or getattr(settings, "AWS_SECRET_ACCESS_KEY", None)
    region = _resolve_region()

    if access_key and secret_key:
        session = boto3.session.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        return session.client("s3")

    # 키를 명시하지 않으면 환경변수/자격증명 파일/IAM Role에서 자동 탐색
    return boto3.client("s3", region_name=region)


# 하위 호환
client_s3 = get_s3_client()

