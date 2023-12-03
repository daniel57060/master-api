import asyncio
from typing import Optional
from asyncpg import CannotConnectNowError
from databases import Database

from .env import env
from .exceptions import NotFoundError


async def connect_to_database() -> Database:
    database = Database(env.database_url)

    # https://stackoverflow.com/questions/69381579/unable-to-start-fastapi-server-with-postgresql-using-docker-compose
    max_tries = 5
    tries = 0
    up = False
    last_error = None
    while tries < max_tries and not up:
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
        if last_error is not None:
            raise last_error
        raise Exception(f"Could not connect to database after {max_tries} tries")

    return database


async def close_database(database: Database) -> None:
    await database.disconnect()


async def init_database() -> None:
    from .models import UserRole
    from .repositories.user_repository import get_user_repository
    from .services.crypt_service import get_crypt_service
    from .services.user_service import get_user_service, UserLogin, UserStore

    database = await connect_to_database()
    crypt_service = get_crypt_service()
    user_repository = get_user_repository(database)
    user_service = get_user_service(crypt_service, user_repository)

    await database.execute("SELECT 1")

    if env.database_engine == "sqlite":
        await database.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
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
                password TEXT NOT NULL,
                role TEXT NOT NULL
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
        await user_service.user_store(UserStore(username="admin", password="admin", role=UserRole.ADMIN))

    await close_database(database)


class DatabaseSingleton:
    instance: Optional[Database] = None

    async def get_instance(self) -> Database:
        if DatabaseSingleton.instance is not None:
            return DatabaseSingleton.instance
        DatabaseSingleton.instance = await connect_to_database()
        return DatabaseSingleton.instance


async def get_database() -> Database:
    database = await DatabaseSingleton().get_instance()
    return database


asyncio.create_task(init_database())
