from fastapi import APIRouter, Depends
from typing import Annotated
from app.models.user_model import User
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()

@router.get("/users/me/", response_model=User, description="토큰 테스트")
async def read_users_me(
        current_user: Annotated[User, Depends(auth_service.get_current_user)],
):
    return current_user
