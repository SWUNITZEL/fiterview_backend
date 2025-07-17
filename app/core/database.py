from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


# MongoDB 연결 설정
client = AsyncIOMotorClient(
    settings.MONGO_DB_URL,
    tlsAllowInvalidCertificates=True
)
database = client[settings.MONGO_DB_NAME]


