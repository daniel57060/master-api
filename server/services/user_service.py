from fastapi import Depends
from pydantic import BaseModel

from ..models import UserModel
from ..db import Database, get_database
from ..exceptions import DomainError, NotFoundError, AlreadyExistsError, UnauthorizedError

from .crypt_service import CryptService, get_crypt_service

class UserSignup(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str


class UserService:
    def __init__(self, db: Database, crypt_service: CryptService) -> None:
        self.db = db
        self.crypt_service = crypt_service
    
    async def user_show(self, user_id: str) -> UserModel:
        user = await self._get_user_by_id(user_id)
        self._fail_if_not_found(user)
        return UserModel(**user).redact()
    
    async def user_login(self, body: UserLogin) -> UserModel:
        user = await self._get_user_by_username(body.username)
        self._fail_if_not_found(user)
        if not self.crypt_service.check_password(body.password, user["password"]):
            raise UnauthorizedError("Invalid credentials")
        return UserModel(**user)

    async def user_signup(self, body: UserSignup) -> UserModel:
        user = await self._get_user_by_username(body.username)
        self._fail_if_found(user)
        query = """INSERT INTO user (username, password) VALUES (:username, :password)"""
        user_id = await self.db.execute(query, {
            "username": body.username,
            "password": self.crypt_service.hash_password(body.password)
        })
        return await self.user_show(user_id)

    async def _get_user_by_username(self, username: str):
        query = """SELECT * FROM user WHERE username = :username"""
        data = await self.db.fetch_one(query, {"username": username})
        return data

    async def _get_user_by_id(self, user_id: str):
        query = """SELECT * FROM user WHERE id = :user_id"""
        data = await self.db.fetch_one(query, {"user_id": user_id})
        return data

    def _fail_if_not_found(self, data):
        if not data:
            raise NotFoundError("User not found")

    def _fail_if_found(self, data):
        if data:
            raise AlreadyExistsError("User already exists")

def get_user_service(db = Depends(get_database), crypt_service = Depends(get_crypt_service)) -> UserService:
    return UserService(db, crypt_service)
