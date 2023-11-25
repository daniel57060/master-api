from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from .user_service import UserService, get_user_service

from ..env import env
from ..models import UserModel

class TokenData(BaseModel):
    user_id: int
    type: str
    user: UserModel

JWT_ALGORITHM = 'HS256'
JWT_SECRET_KEY = env.jwt_secret
JWT_EXPIRES_IN = env.jwt_expires_in
JWT_REFRESH_EXPIRES_IN = env.jwt_refresh_expires_in

oauth2_schema = OAuth2PasswordBearer(tokenUrl='/api/auth/login')

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

    def decode_token(self, token: str) -> TokenData:
        try:
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=JWT_ALGORITHM)
            user_id = data['sub']
            user = self.user_service.user_show(user_id)
            if user.version != data.get('version'):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Token expired',
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return TokenData(user_id=user_id, user=user,
                            type=data.get('typ', 'access_token'))
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )

def get_jwt_service(user_service = Depends(get_user_service)) -> JwtService:
    return JwtService(user_service)
