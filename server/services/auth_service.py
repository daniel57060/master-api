from fastapi import Depends
from pydantic import BaseModel

from ..models import UserModel

from .jwt_service import JwtService, get_jwt_service
from .user_service import UserLogin, UserSignup, UserService, get_user_service


class AuthResponse(BaseModel):
    # https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
    # Required
    refresh_token: str
    access_token: str
    token_type: str = 'bearer'


class AuthService:
    def __init__(self, user_service: UserService, jwt_service: JwtService) -> None:
        self.user_service = user_service
        self.jwt_service = jwt_service

    async def auth_login(self, body: UserLogin) -> AuthResponse:
        user = await self.user_service.user_login(body)
        return self._create_auth_response(user)

    async def auth_signup(self, body: UserLogin) -> AuthResponse:
        user = await self.user_service.user_signup(body)
        return self._create_auth_response(user)

    def _create_auth_response(self, user: UserModel) -> AuthResponse:
        data = {'sub': str(user.id), 'version': user.version}
        access_token = self.jwt_service.create_access_token(data)
        refresh_token = self.jwt_service.create_refresh_token(data)
        return AuthResponse(access_token=access_token, refresh_token=refresh_token)


def get_auth_service(
    user_service = Depends(get_user_service),
    jwt_service = Depends(get_jwt_service),
) -> AuthService:
    return AuthService(user_service, jwt_service)
