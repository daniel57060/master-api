from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile
from server.jobs.process_code_flow_job import ProcessCodeFlowJob, get_process_code_flow_job

from ..models import CodeFlowShow

from ..use_cases.store_code_flow_use_case import StoreCodeFlowUseCase, get_store_code_flow_use_case
from ..services.code_flow_service import CodeFlowService, CodeFlowUpdate, get_code_flow_service
from ..services.jwt_service import TokenData, get_required_token, get_token

router = APIRouter(
    prefix="/code-flow",
    tags=["CodeFlow"],
)


@router.get("/{id}/", description="Show code and flow files")
async def code_flow_show(
    id: int,
    service: CodeFlowService = Depends(get_code_flow_service),
    token: TokenData = Depends(get_required_token),
) -> CodeFlowShow:
    return await service.code_flow_show(id, token.user)


@router.get("/", description="List code and flow files")
async def code_flow_index(
    token: Optional[TokenData] = Depends(get_token),
    service: CodeFlowService = Depends(get_code_flow_service),
) -> List[CodeFlowShow]:
    return await service.code_flow_index(user=token.user if token else None)


@router.post("/", description="Store code and flow files")
async def code_flow_store(
    token: TokenData = Depends(get_required_token),
    code_file: UploadFile = File(...),
    use_case: StoreCodeFlowUseCase = Depends(get_store_code_flow_use_case)
) -> CodeFlowShow:
    return await use_case.execute(token.user, code_file)


@router.put("/{id}/", description="Update code and flow files")
async def code_flow_update(
    id: int,
    body: CodeFlowUpdate,
    token: TokenData = Depends(get_required_token),
    service: CodeFlowService = Depends(get_code_flow_service),
    job: ProcessCodeFlowJob = Depends(get_process_code_flow_job),
) -> CodeFlowShow:
    data = await service.code_flow_update(id, token.user, body)
    if body.processed == False:
        job.create_job(data)
    return data


@router.delete("/{id}/", description="Delete code and flow files")
async def code_flow_delete(
    id: int,
    token: TokenData = Depends(get_required_token),
    service: CodeFlowService = Depends(get_code_flow_service),
) -> None:
    return await service.code_flow_delete(id, token.user)
