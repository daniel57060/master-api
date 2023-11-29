
from databases import Database
from fastapi import Depends
from pydantic import BaseModel
from typing import List, Optional

from ..db import get_database
from ..exceptions import AlreadyExistsError, DomainError, ForbiddenError, NotFoundError, UnauthorizedError
from ..models import CodeFlowModel, UserModel
from ..repositories.code_flow_repository import CodeFlowInsert, CodeFlowRepository
from ..resources import Resources


class CodeFlowStore(BaseModel):
    name: str
    file_id: str
    user_id: int


class CodeFlowUpdate(BaseModel):
    name: Optional[str] = None
    processed: Optional[bool] = None


class CodeFlowService:
    def __init__(self, code_flow_repository: CodeFlowRepository) -> None:
        self.code_flow_repository = code_flow_repository

    async def code_flow_show(self, id: int, user: UserModel) -> CodeFlowModel:
        data = await self.code_flow_repository.get_by_id(id)
        data = self._fail_if_not_found(data)
        if data.user_id != user.id and data.private:
            raise UnauthorizedError("You are not the owner of this CodeFlow")
        return data

    async def code_flow_index(self, user: Optional[UserModel]) -> List[CodeFlowModel]:
        if user is not None:
            return await self.code_flow_repository.get_all_public_and_private(user.id)
        else:
            return await self.code_flow_repository.get_all_public()

    async def code_flow_store(self, body: CodeFlowStore) -> int:
        return await self.code_flow_repository.insert(CodeFlowInsert(
            name=body.name,
            file_id=body.file_id,
            user_id=body.user_id
        ))

    async def code_flow_update(self, id: int, user: UserModel, body: CodeFlowUpdate) -> CodeFlowModel:
        data = await self.code_flow_repository.get_by_id(id)
        data = self._fail_if_not_found(data)
        if data.user_id != user.id:
            raise ForbiddenError(f"You are not the owner of this CodeFlow")

        updated = await self.code_flow_repository.update(id, body)
        if not updated:
            raise DomainError("Nothing to update")

        data = await self.code_flow_repository.get_by_id(id)
        return self._fail_if_not_found(data)

    async def code_flow_delete(self, id: int, user: UserModel) -> None:
        data = await self.code_flow_show(id, user)
        self._fail_if_not_found(data)
        if data.user_id != user.id:
            raise UnauthorizedError("You are not the owner of this CodeFlow")
        (Resources.FILES / f"{data.file_id}_o.c").unlink()
        (Resources.FILES / f"{data.file_id}_t.c").unlink()
        (Resources.FILES / f"{data.file_id}_t.json").unlink(missing_ok=True)
        await self.code_flow_repository.delete(id)

    def _fail_if_not_found(self, data: CodeFlowModel | None) -> CodeFlowModel:
        if not data:
            raise NotFoundError("CodeFlow not found")
        return data


def get_code_flow_service(db: Database = Depends(get_database)) -> CodeFlowService:
    return CodeFlowService(db)
