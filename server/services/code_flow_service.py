
from typing import List, Optional
from databases import Database
from fastapi import Depends
from pydantic import BaseModel

from server.exceptions import NotFoundError

from ..db import get_database
from ..models import CodeFlowModel, CodeFlowShow


class CodeFlowStore(BaseModel):
    name: str
    code_path: str
    flow_path: str


class CodeFlowService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def code_flow_show(self, id: int) -> CodeFlowShow:
        data = await self.code_flow_index(id=id)
        self._fail_if_not_found(data)
        return data[0]

    async def code_flow_index(self,  **values) -> List[CodeFlowShow]:
        query = """SELECT * FROM code_flow WHERE 1=1"""
        for key in values.keys():
            query += f""" AND {key} = :{key}"""
        data = await self.db.fetch_all(query, values)
        return [CodeFlowShow(**item) for item in data]

    async def code_flow_store(self, body: CodeFlowStore) -> CodeFlowShow:
        data = await self.db.execute("""
            INSERT INTO code_flow (name, code_path, flow_path)
            VALUES (:name, :code_path, :flow_path)
        """, body.model_dump())
        data = await self.code_flow_show(data)
        return data

    def _fail_if_not_found(self, data):
        if not data:
            raise NotFoundError("CodeFlow not found")


def get_code_flow_service(db: Database = Depends(get_database)):
    yield CodeFlowService(db)
