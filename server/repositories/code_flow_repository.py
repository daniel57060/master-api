from databases import Database
from databases.interfaces import Record
from fastapi import Depends
from pydantic import BaseModel
from typing import List, Optional

from ..db import get_database
from ..models import CodeFlowModel


class CodeFlowInsert(BaseModel):
    name: str
    file_id: str
    user_id: int


class CodeFlowUpdate(BaseModel):
    name: Optional[str] = None
    processed: Optional[bool] = None


class CodeFlowRepository:
    def __init__(self, db: Database) -> None:
        self.db = db
    
    async def insert(self, data: CodeFlowInsert) -> int:
        return await self.db.execute("""
            INSERT INTO code_flow (name, file_id, processed, flow_error, user_id, private)
            VALUES (:name, :file_id, FALSE, NULL, :user_id, TRUE)
        """, data.model_dump())

    async def update(self, id: int, data: CodeFlowUpdate) -> bool:
        values = data.model_dump(exclude_unset=True)
        if not values:
            return False
        query = """UPDATE code_flow SET """
        query += ", ".join([f"{key} = :{key}" for key in values])
        query += f" WHERE id = :id"
        result = await self.db.execute(query, {"id": id, **values})
        print(result)
        return True
    
    async def update_processed(self, id: int, error: Optional[str] = None) -> None:
        query = 'UPDATE code_flow SET processed = TRUE, flow_error = :error WHERE id = :id'
        result = await self.db.execute(query, {"id": id, "error": error})
        print(result)

    async def delete(self, id: int) -> None:
        result = await self.db.execute("DELETE FROM code_flow WHERE id = :id", {"id": id})
        print(result)

    async def get_all_public(self) -> List[CodeFlowModel]:
        query = """SELECT * FROM code_flow WHERE private = FALSE"""
        data = await self.db.fetch_all(query)
        return [CodeFlowModel(**item) for item in data]
    
    async def get_all_public_and_private(self, user_id: int) -> List[CodeFlowModel]:
        query = """SELECT * FROM code_flow WHERE private = FALSE OR user_id = :user_id"""
        data = await self.db.fetch_all(query, {"user_id": user_id})
        return [CodeFlowModel(**item) for item in data]
    
    async def get_all_unprocessed(self) -> List[CodeFlowModel]:
        query = """SELECT * FROM code_flow WHERE processed = FALSE"""
        data = await self.db.fetch_all(query)
        return [CodeFlowModel(**item) for item in data]
    
    async def get_by_id(self, id: int) -> CodeFlowModel | None:
        query = """SELECT * FROM code_flow WHERE id = :id"""
        data = await self.db.fetch_one(query, {"id": id})
        return self._to_model(data)
    
    async def get_by_name(self, name: str) -> CodeFlowModel | None:
        query = """SELECT * FROM code_flow WHERE name = :name"""
        data = await self.db.fetch_one(query, {"name": name})
        return self._to_model(data)
    
    def _to_model(self, data: Record | None) -> CodeFlowModel | None:
        if data is None:
            return None
        return CodeFlowModel(**data)


def get_code_flow_repository(db: Database = Depends(get_database)) -> CodeFlowRepository:
    return CodeFlowRepository(db)
