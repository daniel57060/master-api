import logging
from typing import Generic, List, Optional, TypeVar

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

import subprocess
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO,
                    format="%(levelname)s: [%(asctime)s] %(name)s: %(message)s")

logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
def read_root():
    return RedirectResponse(url="/docs")


class RunShSubprocess(BaseModel):
    cmd: List[str]
    stdin: Optional[str] = None
    timeout: int = 10


T = TypeVar('T')


class Result(BaseModel, Generic[T]):
    ok: Optional[T] = None
    error: Optional[str] = None


class RunShSubprocessResponse(BaseModel):
    returncode: int
    stdout: str
    stderr: str


@app.post("/v1/run", tags=["Run"])
def run_sh_subprocess(body: RunShSubprocess) -> Result[RunShSubprocessResponse]:
    try:
        logger.info(f"Running command: {body.cmd}")
        cmd = body.cmd
        cmd_process = subprocess.Popen(cmd, text=True, encoding='utf-8',
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        stdout, stderr = cmd_process.communicate(input=body.stdin, timeout=body.timeout)
        result = RunShSubprocessResponse(
            returncode=cmd_process.returncode,
            stdout=stdout,
            stderr=stderr,
        )
        logger.info(f"Command result: {result}")
        return Result(ok=result)
    except subprocess.TimeoutExpired as e:
        logger.error(f"TimeoutExpired: {e}")
        return Result(error=f'TimeoutExpired after {e.timeout} seconds')
    except Exception as e:
        logger.error(f"Exception: {e}")
        return Result(error=str(e))
