from typing import List
from fastapi import APIRouter, Depends, File, UploadFile

from server.models import CodeFlowShow

from ..use_cases.store_code_flow_use_case import StoreCodeFlowUseCase, get_store_code_flow_use_case
from ..services.code_flow_service import CodeFlowService, get_code_flow_service

router = APIRouter(
    prefix="/code-flow",
    tags=["CodeFlow"],
)


@router.get("/{id}/", description="Show code and flow files")
async def code_flow_show(
    id: int = None,
    service: CodeFlowService = Depends(get_code_flow_service)
) -> CodeFlowShow:
    return await service.code_flow_show(id)


@router.get("/", description="List code and flow files")
async def code_flow_index(
    service: CodeFlowService = Depends(get_code_flow_service)
) -> List[CodeFlowShow]:
    return await service.code_flow_index()


@router.post("/", description="Store code and flow files")
async def code_flow_store(
    code_file: UploadFile = File(...),
    use_case: StoreCodeFlowUseCase = Depends(get_store_code_flow_use_case)
) -> CodeFlowShow:
    return await use_case.execute(code_file)
