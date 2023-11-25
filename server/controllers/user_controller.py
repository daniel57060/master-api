from fastapi import APIRouter, Depends

from ..models import UserModel
from ..services.jwt_service import TokenData, get_required_token


router = APIRouter(
    prefix="/user",
    tags=["User"],
)


@router.get("/me")
async def user_me(token: TokenData = Depends(get_required_token)) -> UserModel:
    return token.user
