from fastapi import APIRouter, Depends

from ..services.auth_service import UserLogin, AuthResponse, AuthService, UserSignup, get_auth_service

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/login")
async def auth_login(
    body: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    return await auth_service.auth_login(body)


@router.post("/signup")
async def auth_signup(
    body: UserSignup,
    auth_service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    return await auth_service.auth_signup(body)
