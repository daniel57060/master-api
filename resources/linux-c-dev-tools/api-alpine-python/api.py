from typing import Generic, List, Optional, TypeVar

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

import subprocess
from pydantic import BaseModel

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
        cmd = body.cmd
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, check=False,
            timeout=body.timeout)
    except subprocess.CalledProcessError as e:
        return Result(error=e.stderr)
    except subprocess.TimeoutExpired as e:
        return Result(error=e.stderr)
    except Exception as e:
        return Result(error=str(e))
    return Result(ok=RunShSubprocessResponse(
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr
    ))
