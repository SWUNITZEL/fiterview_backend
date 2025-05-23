from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로딩
load_dotenv()

class Settings(BaseSettings):
    MONGO_DB_NAME: str
    MONGO_DB_URL: str
    CLOVA_SPEECH_SECRET_KEY: str
    CLOVA_SPEECH_URL: str

    CLOVA_OCR_URL: str
    CLOVA_OCR_SECRET_KEY: str
    JWT_SECRET_KEY: str

    AWS_ACCESS_KEY: str
    AWS_SECRET_KEY: str
    S3_BUCKET_NAME: str


settings = Settings()

