from fastapi import APIRouter, Depends

from ..models import UserModel, UserRole
from ..services.jwt_service import TokenData, get_required_token, get_token_with_role
from ..services.user_service import UserService, UserStore, get_user_service


router = APIRouter(
    prefix="/user",
    tags=["User"],
)


@router.post("/")
async def user_store(
    body: UserStore,
    user_service: UserService = Depends(get_user_service),
    _: TokenData = Depends(get_token_with_role(UserRole.ADMIN))
) -> UserModel:
    return await user_service.user_store(body)


@router.get("/me")
async def user_me(token: TokenData = Depends(get_required_token)) -> UserModel:
    return token.user
