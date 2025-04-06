from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로딩
load_dotenv()

class Settings(BaseSettings):
    MONGO_DB_NAME: str
    MONGO_DB_URL: str
    CLOVA_API_SECRET_KEY: str  # 환경 변수에서 API 키를 읽어옵니다.

settings = Settings()

