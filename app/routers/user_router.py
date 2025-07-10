from fastapi import APIRouter, Depends
from typing import Annotated

from app.core.response import CommonResponse
from app.models.user_model import User
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()

@router.get("/users/me/", response_model=User, description="토큰 테스트")
async def read_users_me(
        current_user: Annotated[User, Depends(auth_service.get_current_user)],
):
    return current_user

@router.get("/users/socket-token", description="웹소켓 보안 인증을 위한 토큰 발급")
async def get_socket_token(
        current_user: Annotated[User, Depends(auth_service.get_current_user)]
       ):

    token = auth_service.set_socket_token(current_user["email"])
    return CommonResponse.success_response("토큰 생성 완료", token)