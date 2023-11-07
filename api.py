from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import server.controllers.code_flow_controller
import server.exceptions

app = FastAPI()

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


app.include_router(server.controllers.code_flow_controller.router)

app.mount("/static/files", StaticFiles(directory="files"), name="static")
