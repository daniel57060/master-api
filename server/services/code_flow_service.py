
from typing import List, Optional
from fastapi import Depends
from pydantic import BaseModel

from server.exceptions import AlreadyExistsError, DomainError, NotFoundError, UnauthorizedError
from server.resources import Resources

from ..db import Database, get_database
from ..models import CodeFlowModel, UserModel


class CodeFlowStore(BaseModel):
    name: str
    file_id: str
    user_id: int


class CodeFlowUpdate(BaseModel):
    name: Optional[str] = None
    processed: Optional[bool] = None


class CodeFlowService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def code_flow_show(self, id: int, user: UserModel) -> CodeFlowModel:
        query = """SELECT * FROM code_flow WHERE :id = id"""
        data = await self.db.fetch_one(query, {"id": id})
        self._fail_if_not_found(data)
        if data["user_id"] != user.id and data["private"]:
            raise UnauthorizedError("You are not the owner of this CodeFlow")
        return CodeFlowModel(**data)
    
    async def code_flow_for_store(self, name: str) -> CodeFlowModel:
        query = """SELECT * FROM code_flow WHERE :name = name"""
        data = await self.db.fetch_one(query, {"name": name})
        if data:
            raise AlreadyExistsError(f"CodeFlow with name {name} already exists")

    async def code_flow_index(self, user: Optional[UserModel]) -> List[CodeFlowModel]:
        values = {}
        query = """SELECT * FROM code_flow WHERE 1=1"""
        if user:
            query += """ AND (private = FALSE OR user_id = :user_id)"""
            values["user_id"] = user.id
        else:
            query += """ AND private = FALSE"""
        data = await self.db.fetch_all(query, values)
        return [CodeFlowModel(**item) for item in data]

    async def code_flow_unprocessed(self) -> List[CodeFlowModel]:
        query = """SELECT * FROM code_flow WHERE processed = FALSE"""
        data = await self.db.fetch_all(query)
        return [CodeFlowModel(**item) for item in data]

    async def code_flow_store(self, body: CodeFlowStore) -> int:
        return await self.db.execute("""
            INSERT INTO code_flow (name, file_id, processed, flow_error, user_id, private)
            VALUES (:name, :file_id, FALSE, NULL, :user_id, TRUE)
        """, body.model_dump())

    async def code_flow_update(self, id: int, user: UserModel, body: CodeFlowUpdate) -> CodeFlowModel:
        values = body.model_dump(exclude_unset=True)
        if not values:
            raise DomainError("No values to update")

        data = await self.code_flow_show(id)
        if data.user_id != user.id:
            raise UnauthorizedError("You are not the owner of this CodeFlow")

        values["id"] = id
        query = 'UPDATE code_flow SET '
        updates = [f'{key} = :{key}' for key in values.keys()]
        query += ', '.join(updates)
        query += ' WHERE id = :id'
        await self.db.execute(query, values)
        data = await self.code_flow_show(id)
        return data
    
    async def code_flow_processed(self, id: int, error: Optional[str] = None):
        query = 'UPDATE code_flow SET processed = TRUE, flow_error = :error WHERE id = :id'
        await self.db.execute(query, {"id": id, "error": error})
    
    async def code_flow_delete(self, id: int, user: UserModel) -> None:
        data = await self.code_flow_show(id)
        self._fail_if_not_found(data)
        if data.user_id != user.id:
            raise UnauthorizedError("You are not the owner of this CodeFlow")
        (Resources.FILES / f"{data.file_id}_o.c").unlink()
        (Resources.FILES / f"{data.file_id}_t.c").unlink()
        (Resources.FILES / f"{data.file_id}_t.json").unlink(missing_ok=True)
        await self.db.execute("DELETE FROM code_flow WHERE id = :id", {"id": id})

    def _fail_if_not_found(self, data):
        if not data:
            raise NotFoundError("CodeFlow not found")


def get_code_flow_service(db: Database = Depends(get_database)):
    yield CodeFlowService(db)
