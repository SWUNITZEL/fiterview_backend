from app.core.config import settings
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"


def decode_token(token: str) -> dict:
    try:
        print("jwt: ", token)
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise ExpiredSignatureError("Token has expired")
    except InvalidTokenError as e:
        print("InvalidTokenError: ",e)
        raise InvalidTokenError("Invalid token")
