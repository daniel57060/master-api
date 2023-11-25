from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from ..services.auth_service import UserLogin, AuthResponse, AuthService, UserSignup, get_auth_service
from ..services.jwt_service import TokenData, get_token

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/login")
async def auth_login(
    form: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    body = UserLogin(username=form.username, password=form.password)
    return await auth_service.auth_login(body)


@router.post("/signup")
async def auth_signup(
    body: UserSignup,
    auth_service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    return await auth_service.auth_signup(body)


@router.get("/is-logged-in")
async def auth_is_logged_in(
    token: Optional[TokenData] = Depends(get_token),
) -> bool:
    return token is not None