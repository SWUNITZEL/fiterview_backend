from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import ExpiredSignatureError, InvalidTokenError
from typing import Annotated

from app.core.security import decode_token
from app.repository.user_repository import find_user  # 별도 모듈로 분리 추천


bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)]
):

    token = credentials.credentials
    try:
        payload = decode_token(token)
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await find_user(email=email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
