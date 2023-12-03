from databases import Database
from databases.interfaces import Record
from fastapi import Depends
from pydantic import BaseModel

from ..db import get_database
from ..models import UserModel, UserRole


class UserInsert(BaseModel):
    username: str
    password: str
    role: UserRole


class UserRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def insert(self, user: UserInsert) -> int:
        query = """
            INSERT INTO users (username, password, role)
            VALUES (:username, :password, :role)
            RETURNING id
        """
        return await self.db.execute(query, {
            "username": user.username,
            "password": user.password,
            "role": user.role.value,
        })

    async def get_by_username(self, username: str) -> UserModel | None:
        query = """SELECT * FROM users WHERE username = :username"""
        data = await self.db.fetch_one(query, {"username": username})
        return self._to_model(data)

    async def get_by_id(self, user_id: int) -> UserModel | None:
        query = """SELECT * FROM users WHERE id = :user_id"""
        data = await self.db.fetch_one(query, {"user_id": user_id})
        return self._to_model(data)

    def _to_model(self, data: Record | None) -> UserModel | None:
        if data is None:
            return None
        return UserModel(**dict(data))


def get_user_repository(db: Database = Depends(get_database)) -> UserRepository:
    return UserRepository(db)
