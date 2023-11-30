from pydantic import BaseModel
import os
import dotenv

from .resources import Resources


class Env(BaseModel):
    c_runner_url: str
    database_engine: str
    database_url: str
    jwt_secret: str
    jwt_expires_in: int
    jwt_refresh_expires_in: int


dotenv.load_dotenv()
env = Env(
    c_runner_url=os.environ.get('C_RUNNER_URL', 'http://localhost:8001'),
    database_engine = os.environ.get("DATABASE_ENGINE", "sqlite"),
    database_url=os.environ.get(
        'DATABASE_URL', "sqlite+aiosqlite:///" + str(Resources.DATABASE)),
    jwt_secret = os.environ.get("JWT_SECRET", "secret"),
    jwt_expires_in = int(os.environ.get("JWT_EXPIRES_IN", 1 * 60 * 60 * 1000)), # 1 hour
    jwt_refresh_expires_in = int(os.environ.get("JWT_REFRESH_EXPIRES_IN", 7 * 24 * 60 * 60 * 1000)), # 7 days
)
