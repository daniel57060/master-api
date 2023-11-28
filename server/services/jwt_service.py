from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from .user_service import UserService, get_user_service

from ..env import env
from ..exceptions import UnauthorizedError
from ..models import UserModel

class TokenData(BaseModel):
    user_id: int
    type: str
    user: UserModel

JWT_ALGORITHM = 'HS256'
JWT_SECRET_KEY = env.jwt_secret
JWT_EXPIRES_IN = env.jwt_expires_in
JWT_REFRESH_EXPIRES_IN = env.jwt_refresh_expires_in

oauth2_schema = OAuth2PasswordBearer(tokenUrl='/auth/login', auto_error=False)

class JwtService:
    def __init__(self, user_service: UserService) -> None:
        self.user_service = user_service

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
            user = await self.user_service.user_show(user_id)
            if user.version != data.get('version'):
                raise UnauthorizedError('Token version mismatch')
            return TokenData(user_id=user_id, user=user,
                            type=data.get('typ', 'access_token'))
        except JWTError as e:
            raise UnauthorizedError(str(e))

def get_jwt_service(user_service = Depends(get_user_service)) -> JwtService:
    return JwtService(user_service)


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