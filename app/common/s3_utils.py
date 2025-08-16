from botocore.exceptions import NoCredentialsError, ClientError
from app.aws import get_s3_client

def generate_presigned_url(bucket: str, key: str, expires_in: int = 60 * 60 * 24 * 7) -> str:
    """
    S3 객체에 접근할 수 있는 presigned URL 생성
    - bucket: S3 버킷 이름
    - key: S3 객체 키 (폴더 포함 경로)
    - expires_in: URL 만료 시간(초)  # 7일(604800초)
    """
    s3 = get_s3_client()

    try:
        return s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
    except NoCredentialsError:
        raise RuntimeError("AWS 자격 증명을 찾을 수 없습니다. 환경변수를 확인하세요.")
    except ClientError as e:
        raise RuntimeError(f"Presigned URL 생성 실패: {e}")
