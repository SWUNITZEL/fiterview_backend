from fastapi import APIRouter, Depends
from typing import Annotated
from app.models.User import User
from app.services.auth_service import get_current_user

router = APIRouter()


@router.get("/users/me/", response_model=User, description="토큰 테스트")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await current_user