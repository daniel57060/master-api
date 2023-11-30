import asyncio
from typing import AsyncIterator
from asyncpg import CannotConnectNowError
from databases import Database
from fastapi import Depends

from .env import env
from .exceptions import NotFoundError


async def connect_to_database() -> Database:
    database = Database(env.database_url)

    # https://stackoverflow.com/questions/69381579/unable-to-start-fastapi-server-with-postgresql-using-docker-compose
    tries = 0
    up = False
    last_error = None
    while tries < 3 and not up:
        try:
            await database.connect()
            up = True
            break
        except CannotConnectNowError as e:
            last_error = e
        except ConnectionRefusedError as e:
            last_error = e
        tries += 1
        await asyncio.sleep(1)
    if not up:
        raise last_error

    return database


async def close_database(database: Database) -> None:
    await database.disconnect()


async def init_database() -> None:
    from .services.crypt_service import CryptService
    from .services.user_service import UserService, UserSignup, UserLogin
    from .repositories.user_repository import UserRepository

    database = await connect_to_database()
    crypt_service = CryptService()
    user_repository = UserRepository(database)
    user_service = UserService(crypt_service, user_repository)

    await database.execute("SELECT 1")

    if env.database_engine == "sqlite":
        await database.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )"""
        )
        await database.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS user_username_idx ON users (username)""")

        await database.execute(
            """CREATE TABLE IF NOT EXISTS code_flow (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    elif env.database_engine == "postgresql":
        await database.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )"""
        )
        await database.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS user_username_idx ON users (username)""")

        await database.execute(
            """CREATE TABLE IF NOT EXISTS code_flow (
                id SERIAL PRIMARY KEY,
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
    else:
        raise Exception("Unknown db_engine: " + env.database_engine)
    
    try:
        await user_service.user_login(UserLogin(username="admin", password="admin"))
    except NotFoundError:
        await user_service.user_signup(UserSignup(username="admin", password="admin"))

    await close_database(database)

async def get_database(database: Database = Depends(connect_to_database)) -> AsyncIterator[Database]:
    try:
        yield database
    finally:
        await close_database(database)


asyncio.create_task(init_database())