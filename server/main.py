from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator
from fastapi import FastAPI, Response
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from mimetypes import guess_type

import server.controllers.auth_controller
import server.controllers.code_flow_controller
import server.controllers.user_controller
import server.exceptions

from server.resources import Resources
from server.exceptions import NotFoundError

logging.basicConfig(level=logging.INFO,
                    format="%(levelname)s: [%(asctime)s] %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    from server.database.init_database import init_database
    from server.database.connection import DatabaseSingleton

    database = DatabaseSingleton()
    connection = await database.get_instance()
    await init_database(connection)

    yield

    await database.close_instance()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

server.exceptions.configure(app)


@app.get("/", tags=["Root"])
def read_root():
    return RedirectResponse(url="/docs")


@app.get("/static/files/{file_path:path}", include_in_schema=False)
def read_static_file(file_path: str) -> Response:
    # https://stackoverflow.com/questions/62455652/how-to-serve-static-files-in-fastapi
    full_path = Resources.FILES / file_path
    if not full_path.exists():
        raise NotFoundError(f"File {file_path} not found")

    with open(full_path) as f:
        content = f.read()

    content_type, _ = guess_type(full_path)
    return Response(content, media_type=content_type)


app.include_router(server.controllers.auth_controller.router)
app.include_router(server.controllers.code_flow_controller.router)
app.include_router(server.controllers.user_controller.router)
