from datetime import datetime, timedelta

from app.core.config import settings
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

SECRET_KEY = settings.JWT_SECRET_KEY
SOCKET_SECRET_KEY = settings.JWT_SOCKET_SECRET_KEY
ALGORITHM = "HS256"


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise ExpiredSignatureError("Token has expired")
    except InvalidTokenError as e:
        print("InvalidTokenError: ",e)
        raise InvalidTokenError("Invalid token")


# 웹소켓 토큰 생성 메서드
def create_socket_token(user_email: str) -> str:
    expire = datetime.utcnow() + timedelta(seconds=30)
    to_encode = {"email": user_email, "exp": expire}
    return jwt.encode(to_encode, SOCKET_SECRET_KEY, algorithm=ALGORITHM)

# 웹소켓 토큰 인증 메서드
def decode_socket_token(token: str) -> dict:
    try:
        return jwt.decode(token, SOCKET_SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise ExpiredSignatureError("Token has expired")
    except InvalidTokenError as e:
        print("InvalidTokenError: ",e)
        raise InvalidTokenError("Invalid token")