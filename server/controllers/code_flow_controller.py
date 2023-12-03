from fastapi import APIRouter, Depends, File, UploadFile
from typing import List, Optional

from ..models import CodeFlowShow, UserRole
from ..repositories.code_flow_repository import CodeFlowUpdate
from ..services.code_flow_service import CodeFlowService, get_code_flow_service
from ..services.jwt_service import TokenData, get_required_token, get_token, get_token_with_role
from ..use_cases.store_code_flow_use_case import StoreCodeFlowUseCase, get_store_code_flow_use_case


router = APIRouter(
    prefix="/code-flow",
    tags=["CodeFlow"],
)
get_token_with_router_roles = get_token_with_role(UserRole.ADMIN, UserRole.PROFESSOR)


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
    token: TokenData = Depends(get_token_with_router_roles),
    code_file: UploadFile = File(...),
    use_case: StoreCodeFlowUseCase = Depends(get_store_code_flow_use_case)
) -> CodeFlowShow:
    return await use_case.execute(token.user, code_file)


@router.put("/{id}/", description="Update code and flow files")
async def code_flow_update(
    id: int,
    body: CodeFlowUpdate,
    token: TokenData = Depends(get_token_with_router_roles),
    service: CodeFlowService = Depends(get_code_flow_service),
) -> CodeFlowShow:
    return await service.code_flow_update(id, token.user, body)


@router.delete("/{id}/", description="Delete code and flow files")
async def code_flow_delete(
    id: int,
    token: TokenData = Depends(get_token_with_router_roles),
    service: CodeFlowService = Depends(get_code_flow_service),
) -> None:
    return await service.code_flow_delete(id, token.user)
