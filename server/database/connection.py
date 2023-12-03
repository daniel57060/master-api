import asyncio
from typing import Optional
from asyncpg import CannotConnectNowError
from databases import Database

from ..env import env


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



class DatabaseSingleton:
    instance: Optional[Database] = None

    async def get_instance(self) -> Database:
        if DatabaseSingleton.instance is not None:
            return DatabaseSingleton.instance
        DatabaseSingleton.instance = await connect_to_database()
        return DatabaseSingleton.instance
    
    async def close_instance(self) -> None:
        if DatabaseSingleton.instance is not None:
            await close_database(DatabaseSingleton.instance)
            DatabaseSingleton.instance = None


async def get_database() -> Database:
    database = await DatabaseSingleton().get_instance()
    return database


