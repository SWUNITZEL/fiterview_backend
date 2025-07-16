from fastapi import HTTPException, Depends, FastAPI
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import ExpiredSignatureError, InvalidTokenError
from typing import Annotated


from app.core.exceptions.base import AppException
from app.core.security import decode_token, decode_socket_token, create_socket_token
from app.repository.user_repository import UserRepository  # 별도 모듈로 분리 추천


class AuthService:
    bearer_scheme = HTTPBearer(auto_error=False)
    user_repository = UserRepository()

    async def get_current_user(
        self,
        credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)]
    ):
        if credentials is None:
            print(" credentials is None")
            raise AppException(status_code=401, message="token is missing")

        token = credentials.credentials
        try:
            payload = decode_token(token)
            email = payload.get("email")
            if not email:
                raise AppException(status_code=401, message="Invalid token payload")
        except ExpiredSignatureError:
            raise AppException(status_code=401, message="Token has expired")
        except InvalidTokenError:
            raise AppException(status_code=401, message="Invalid token")

        user = await self.user_repository.find_user(email)
        if not user:
            raise AppException(status_code=401, message="User not found")

        return user

    # 웹소켓 토큰 생성 후 반환
    def set_socket_token(
            self,
            user_email: str
    ):
        return create_socket_token(user_email)

    async def verify_socket_token(
            self,
            token: str
    ):
        try:
            payload = decode_socket_token(token)
            email = payload.get("email")
            print("email: ", email)
            if not email:
                raise AppException(status_code=401, message="Invalid token payload")
        except ExpiredSignatureError:
            raise AppException(status_code=401, message="Token has expired")
        except InvalidTokenError:
            raise AppException(status_code=401, message="Invalid token")

        user = await self.user_repository.find_user(email)

        print("verify_socket_token: ", user["email"])
        if not user:
            raise AppException(status_code=401, message="User not found")

