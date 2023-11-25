
from typing import List, Optional
from fastapi import Depends
from pydantic import BaseModel

from server.exceptions import DomainError, NotFoundError
from server.resources import Resources

from ..db import Database, get_database
from ..models import CodeFlowModel


class CodeFlowStore(BaseModel):
    name: str
    file_id: str


class CodeFlowUpdate(BaseModel):
    name: Optional[str]
    json_path: Optional[str]


class CodeFlowService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def code_flow_show(self, id: int) -> CodeFlowModel:
        data = await self.code_flow_index(id=id)
        self._fail_if_not_found(data)
        return data[0]

    async def code_flow_index(self,  **values) -> List[CodeFlowModel]:
        query = """SELECT * FROM code_flow WHERE 1=1"""
        for key, value in list(values.items()):
            if value is None:
                query += f""" AND {key} IS NULL"""
                del values[key]
            else:
                query += f""" AND {key} = :{key}"""
        data = await self.db.fetch_all(query, values)
        return [CodeFlowModel(**item) for item in data]

    async def code_flow_store(self, body: CodeFlowStore) -> CodeFlowModel:
        data = await self.db.execute("""
            INSERT INTO code_flow (name, file_id, processed, flow_error)
            VALUES (:name, :file_id, FALSE, NULL)
        """, body.model_dump())
        data = await self.code_flow_show(data)
        return data

    async def code_flow_update(self, id: int, **values) -> CodeFlowModel:
        if not values:
            raise DomainError("No values to update")
        values["id"] = id
        query = 'UPDATE code_flow SET '
        updates = [f'{key} = :{key}' for key in values.keys()]
        query += ', '.join(updates)
        query += ' WHERE id = :id'
        data = await self.db.execute(query, values)
        if data == 0:
            raise NotFoundError("CodeFlow not found")
        data = await self.code_flow_show(id)
        return data

    async def code_flow_delete(self, id: int) -> None:
        data = await self.code_flow_index(id=id)
        self._fail_if_not_found(data)
        data = data[0]
        files = [
            Resources.FILES / f"{data.file_id}_o.c",
            Resources.FILES / f"{data.file_id}_t.c",
            Resources.FILES / f"{data.file_id}_t.json",
        ]
        for it in files:
            it.unlink(missing_ok=True)
        await self.db.execute("DELETE FROM code_flow WHERE id = :id", {"id": id})
        return data

    def _fail_if_not_found(self, data):
        if not data:
            raise NotFoundError("CodeFlow not found")


def get_code_flow_service(db: Database = Depends(get_database)):
    yield CodeFlowService(db)
