import logging
from databases import Database

from ..env import env
from ..exceptions import AlreadyExistsError, NotFoundError
from ..models import UserRole
from ..repositories.user_repository import get_user_repository
from ..services.crypt_service import get_crypt_service
from ..services.user_service import UserUpdateDiff, get_user_service, UserStore

logger = logging.getLogger(__name__)

async def init_database(database: Database) -> None:
    crypt_service = get_crypt_service()
    user_repository = get_user_repository(database)
    user_service = get_user_service(crypt_service, user_repository)

    logger.info("Initializing database")
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
                flow_error TEXT,
                input TEXT
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
                flow_error TEXT,
                input TEXT
            )""")
        await database.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS code_flow_unique_idx ON code_flow (user_id, name)""")
        await database.execute(
            """CREATE INDEX IF NOT EXISTS code_flow_private_idx ON code_flow (private)""")
    else:
        raise Exception("Unknown db_engine: " + env.database_engine)
    
    user = None
    username = "admin"
    password = env.admin_password
    try:
        user = await user_repository.get_by_username(username)
    except NotFoundError:
        logger.warn("Admin user not found")

    if user is None:
        try:
            user = await user_service.user_store(UserStore(username=username, password=password, role=UserRole.ADMIN))
        except AlreadyExistsError:
            logger.warn("Admin user already exists, but password is different")

        if user is None:
            await user_service.user_update(user.id, UserUpdateDiff(password=password))
            logger.info("Admin user updated")

    logger.info("Database initialized")
