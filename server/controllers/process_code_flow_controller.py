
from typing import List
from fastapi import APIRouter, Depends

from ..jobs.process_code_flow_job import ProcessCodeFlowJob, get_process_code_flow_job
from ..models import CodeFlowShow


router = APIRouter(
    prefix="/process-code-flow",
    tags=["ProcessCodeFlow"],
)


@router.get("/", description="List code and flow files")
async def code_flow_index(
    job: ProcessCodeFlowJob = Depends(get_process_code_flow_job)
) -> List[CodeFlowShow]:
    return job.get_list()
