from datetime import datetime, timedelta
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Callable, Optional

from ..env import env
from ..exceptions import UnauthorizedError
from ..models import UserModel, UserRole
from ..repositories.user_repository import UserRepository, get_user_repository


JWT_ALGORITHM = 'HS256'
JWT_SECRET_KEY = env.jwt_secret
JWT_EXPIRES_IN = env.jwt_expires_in
JWT_REFRESH_EXPIRES_IN = env.jwt_refresh_expires_in

oauth2_schema = OAuth2PasswordBearer(tokenUrl='/auth/login', auto_error=False)


class TokenData(BaseModel):
    user_id: int
    type: str
    user: UserModel


class JwtService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def _create_token(self, data: dict, milliseconds: int, typ: str) -> str:
        data['exp'] = datetime.now() + timedelta(milliseconds=milliseconds)
        data['typ'] = typ
        token = jwt.encode(data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token

    def create_access_token(self, data: dict) -> str:
        return self._create_token(data, JWT_EXPIRES_IN, 'access_token')

    def create_refresh_token(self, data: dict) -> str:
        return self._create_token(data, JWT_REFRESH_EXPIRES_IN, 'refresh_token')

    async def decode_token(self, token: str) -> TokenData:
        try:
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=JWT_ALGORITHM)
            user_id = int(data['sub'])
            user = await self.user_repository.get_by_id(user_id)
            if user is None:
                raise UnauthorizedError('Invalid token')
            if user.version != data.get('version'):
                raise UnauthorizedError('Token version mismatch')
            return TokenData(user_id=user_id, user=user,
                            type=data.get('typ', 'access_token'))
        except JWTError as e:
            raise UnauthorizedError(str(e))


def get_jwt_service(user_repository: UserRepository = Depends(get_user_repository)) -> JwtService:
    return JwtService(user_repository)


async def get_required_token(
    jwt_service: JwtService = Depends(get_jwt_service),
    token: Optional[str] = Depends(oauth2_schema)
) -> TokenData:
    if not token:
        raise UnauthorizedError('Not authenticated')
    return await jwt_service.decode_token(token)


async def get_token(
    jwt_service: JwtService = Depends(get_jwt_service),
    token: Optional[str] = Depends(oauth2_schema)
) -> Optional[TokenData]:
    if not token:
        return None
    return await jwt_service.decode_token(token)


def get_token_with_role(role: UserRole, *roles: UserRole) -> Callable[[TokenData], TokenData]:
    all_roles = list(roles)
    all_roles.append(role)
    def _get_token_with_role(token: TokenData = Depends(get_required_token)) -> TokenData:
        if all_roles and token.user.role not in all_roles:
            raise UnauthorizedError('Not authorized')
        return token
    return _get_token_with_role
