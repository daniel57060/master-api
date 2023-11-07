from databases import Database
from fastapi import Depends

from server.resources import Resources


async def connect_to_database():
    DATABASE_URL = "sqlite:///" + str(Resources.DATABASE)
    database = Database(DATABASE_URL)
    await database.connect()
    return database


async def close_database(database: Database):
    await database.disconnect()


async def init_database(database: Database):
    await database.execute("SELECT 1")
    await database.execute(
        """CREATE TABLE IF NOT EXISTS code_flow (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            file_id TEXT NOT NULL,
            processed BOOLEAN NOT NULL,    
            flow_error TEXT
        )""")
    await database.execute(
        """CREATE UNIQUE INDEX IF NOT EXISTS code_flow_name_idx ON code_flow (name)""")


async def get_database(database: Database = Depends(connect_to_database)):
    try:
        await init_database(database)
        yield database
    finally:
        await close_database(database)
