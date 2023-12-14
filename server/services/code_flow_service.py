
from fastapi import Depends
from pydantic import BaseModel
from typing import List, Optional

from ..exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from ..jobs.process_code_flow_job import ProcessCodeFlowJob, get_process_code_flow_job
from ..mappers import CodeFlowShowMapper
from ..models import CodeFlowModel, CodeFlowShow, UserModel
from ..repositories.code_flow_repository import CodeFlowRepository, CodeFlowUpdate, get_code_flow_repository
from ..resources import Resources


class CodeFlowStore(BaseModel):
    name: str
    file_id: str
    user_id: int


class CodeFlowService:
    def __init__(self, code_flow_repository: CodeFlowRepository, process_code_flow_job: ProcessCodeFlowJob) -> None:
        self.code_flow_repository = code_flow_repository
        self.process_code_flow_job = process_code_flow_job

    async def code_flow_show(self, id: int, user: UserModel) -> CodeFlowShow:
        data = await self.code_flow_repository.get_by_id(id)
        data = self._fail_if_not_found(data)
        if data.user_id != user.id and data.private:
            raise UnauthorizedError("You are not the owner of this CodeFlow")
        return CodeFlowShowMapper.from_model(data)

    async def code_flow_index(self, user: Optional[UserModel]) -> List[CodeFlowShow]:
        if user is not None:
            data = await self.code_flow_repository.get_all_public_and_private(user.id)
        else:
            data = await self.code_flow_repository.get_all_public()
        return CodeFlowShowMapper.from_all_models(data)

    async def code_flow_update(self, id: int, user: UserModel, body: CodeFlowUpdate) -> CodeFlowShow:
        data = await self.code_flow_repository.get_by_id(id)
        data = self._fail_if_not_found(data)
        if data.user_id != user.id:
            raise ForbiddenError(f"You are not the owner of this CodeFlow")

        updated = await self.code_flow_repository.update(id, body)
        if updated:
            data = await self.code_flow_repository.get_by_id(id)
            data = self._fail_if_not_found(data)

        if body.processed == False:
            self.process_code_flow_job.create_job(data)
        return CodeFlowShowMapper.from_model(data)

    async def code_flow_delete(self, id: int, user: UserModel) -> None:
        data = await self.code_flow_repository.get_by_id(id)
        data = self._fail_if_not_found(data)
        if data.user_id != user.id:
            raise UnauthorizedError("You are not the owner of this CodeFlow")
        (Resources.FILES / f"{data.file_id}_o.c").unlink(missing_ok=True)
        (Resources.FILES / f"{data.file_id}_t.c").unlink(missing_ok=True)
        (Resources.FILES / f"{data.file_id}_t.json").unlink(missing_ok=True)
        await self.code_flow_repository.delete(id)

    def _fail_if_not_found(self, data: CodeFlowModel | None) -> CodeFlowModel:
        if not data:
            raise NotFoundError("CodeFlow not found")
        return data


def get_code_flow_service(
    code_flow_repository: CodeFlowRepository = Depends(get_code_flow_repository),
    process_code_flow_job: ProcessCodeFlowJob = Depends(get_process_code_flow_job),
) -> CodeFlowService:
    return CodeFlowService(code_flow_repository, process_code_flow_job)
