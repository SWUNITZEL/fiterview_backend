from pydantic import BaseModel


# 사용자
class User(BaseModel):
    email: str
