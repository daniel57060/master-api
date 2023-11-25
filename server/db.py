import asyncio
from databases import Database
from fastapi import Depends

from .env import env
from .exceptions import NotFoundError


async def connect_to_database():
    database = Database(env.database_url)
    await database.connect()
    return database


async def close_database(database: Database):
    await database.disconnect()


async def init_database():
    from .services.crypt_service import CryptService
    from .services.user_service import UserService, UserSignup, UserLogin
    database = await connect_to_database()
    crypt_service = CryptService()
    user_service = UserService(database, crypt_service)

    await database.execute("SELECT 1")

    await database.execute(
        """CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )"""
    )
    await database.execute(
        """CREATE UNIQUE INDEX IF NOT EXISTS user_username_idx ON user (username)""")

    await database.execute(
        """CREATE TABLE IF NOT EXISTS code_flow (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            file_id TEXT NOT NULL,
            processed BOOLEAN NOT NULL,
            user_id INTEGER NOT NULL,
            private BOOLEAN NOT NULL,
            flow_error TEXT
        )""")
    await database.execute(
        """CREATE UNIQUE INDEX IF NOT EXISTS code_flow_unique_idx ON code_flow (user_id, name)""")
    await database.execute(
        """CREATE INDEX IF NOT EXISTS code_flow_private_idx ON code_flow (private)""")
    
    try:
        await user_service.user_login(UserLogin(username="admin", password="admin"))
    except NotFoundError:
        await user_service.user_signup(UserSignup(username="admin", password="admin"))

    await close_database(database)

asyncio.create_task(init_database())

async def get_database(database: Database = Depends(connect_to_database)):
    try:
        yield database
    finally:
        await close_database(database)
