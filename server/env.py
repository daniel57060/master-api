from pydantic import BaseModel
import os

from .resources import Resources


class Env(BaseModel):
    c_runner_url: str
    database_url: str


env = Env(
    c_runner_url=os.environ.get('C_RUNNER_URL', 'http://localhost:5000'),
    database_url=os.environ.get(
        'DATABASE_URL', "sqlite:///" + str(Resources.DATABASE))
)
