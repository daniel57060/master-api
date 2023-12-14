from typing import Optional
from fastapi import Depends
from pydantic import BaseModel

from ..exceptions import NotFoundError, AlreadyExistsError, UnauthorizedError
from ..models import UserModel, UserRole
from ..repositories.user_repository import UserInsert, UserRepository, UserUpdate, get_user_repository

from .crypt_service import CryptService, get_crypt_service


class UserLogin(BaseModel):
    username: str
    password: str


class UserStore(BaseModel):
    username: str
    password: str
    role: UserRole


class UserUpdateDiff(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None


class ChangePassword(BaseModel):
    old_password: str
    new_password: str


class UserService:
    def __init__(self, crypt_service: CryptService, user_repository: UserRepository) -> None:
        self.crypt_service = crypt_service
        self.user_repository = user_repository
    
    async def user_show(self, user_id: int) -> UserModel:
        user = await self.user_repository.get_by_id(user_id)
        user = self._fail_if_not_found(user)
        return user.redact()

    async def user_login(self, body: UserLogin) -> UserModel:
        user = await self.user_repository.get_by_username(body.username)
        user = self._fail_if_not_found(user)
        self.fail_if_not_check_password(body.password, user.password)
        return user.redact()

    def fail_if_not_check_password(self, password: str, password_hashed: str):
        if not self.crypt_service.check_password(password, password_hashed):
            raise UnauthorizedError("Invalid credentials")

    async def user_store(self, body: UserStore) -> UserModel:
        user = await self.user_repository.get_by_username(body.username)
        self._fail_if_found(user)
        user_id = await self.user_repository.insert(UserInsert(
            username=body.username,
            password=self.crypt_service.hash_password(body.password),
            role=body.role
        ))
        return await self.user_show(user_id)
    
    async def user_update_by_id(self, user_id: int, body: UserUpdateDiff) -> UserModel:
        user = await self.user_repository.get_by_id(user_id)
        user = self._fail_if_not_found(user)
        return await self.user_update(user, body)
    
    async def user_update(self, user: UserModel, body: UserUpdateDiff) -> UserModel:
        data = body.model_dump(exclude_unset=True)
        await self.user_repository.update(user.id, UserUpdate(
            username=data['username'] if 'username' in data else user.username,
            password=self.crypt_service.hash_password(data['password']) if 'password' in data else user.password,
            role=data['role'] if 'role' in data else user.role,
        ))
        return await self.user_show(user.id)

    def _fail_if_not_found(self, data: UserModel | None) -> UserModel:
        if not data:
            raise NotFoundError("User not found")
        return data

    def _fail_if_found(self, data):
        if data:
            raise AlreadyExistsError("User already exists")


def get_user_service(
    crypt_service: CryptService = Depends(get_crypt_service),
    user_repository: UserRepository = Depends(get_user_repository)
) -> UserService:
    return UserService(crypt_service, user_repository)
