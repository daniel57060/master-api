from databases import Database
from fastapi import Depends
from pydantic import BaseModel
from typing import List, Optional

from ..database.connection import get_database
from ..models import CodeFlowModel
from ..mappers import CodeFlowMapper


class CodeFlowInsert(BaseModel):
    name: str
    file_id: str
    user_id: int


class CodeFlowUpdate(BaseModel):
    name: Optional[str] = None
    processed: Optional[bool] = None
    private: Optional[bool] = None
    input: Optional[str] = None


class CodeFlowRepository:
    def __init__(self, db: Database) -> None:
        self.db = db
    
    async def insert(self, data: CodeFlowInsert) -> int:
        return await self.db.execute("""
            INSERT INTO code_flow (name, file_id, processed, flow_error, user_id, private)
            VALUES (:name, :file_id, TRUE, 'You need to run', :user_id, TRUE)
            RETURNING id
        """, data.model_dump())

    async def update(self, id: int, data: CodeFlowUpdate) -> bool:
        values = data.model_dump(exclude_unset=True)
        if not values:
            return False
        query = """UPDATE code_flow SET """
        query += ", ".join([f"{key} = :{key}" for key in values])
        query += f" WHERE id = :id"
        result = await self.db.execute(query, {"id": id, **values})
        return result == 1
    
    async def update_processed(self, id: int, error: Optional[str] = None) -> bool:
        query = 'UPDATE code_flow SET processed = TRUE, flow_error = :error WHERE id = :id'
        result = await self.db.execute(query, {"id": id, "error": error})
        return result == 1

    async def delete(self, id: int) -> bool:
        result = await self.db.execute("DELETE FROM code_flow WHERE id = :id", {"id": id})
        return result == 1

    async def get_all_public(self) -> List[CodeFlowModel]:
        query = """SELECT * FROM code_flow WHERE private = FALSE"""
        data = await self.db.fetch_all(query)
        return CodeFlowMapper.from_all_records(data)
    
    async def get_all_public_and_private(self, user_id: int) -> List[CodeFlowModel]:
        query = """SELECT * FROM code_flow WHERE private = FALSE OR user_id = :user_id"""
        data = await self.db.fetch_all(query, {"user_id": user_id})
        return CodeFlowMapper.from_all_records(data)
    
    async def get_all_unprocessed_and_failed(self) -> List[CodeFlowModel]:
        query = """SELECT * FROM code_flow WHERE processed = FALSE OR flow_error IS NOT NULL"""
        data = await self.db.fetch_all(query)
        return CodeFlowMapper.from_all_records(data)
    
    async def get_by_id(self, id: int) -> CodeFlowModel | None:
        query = """SELECT * FROM code_flow WHERE id = :id"""
        data = await self.db.fetch_one(query, {"id": id})
        return CodeFlowMapper.from_record_(data)
    
    async def get_by_user_id_and_name(self, user_id: int, name: str) -> CodeFlowModel | None:
        query = """SELECT * FROM code_flow WHERE user_id = :user_id AND name = :name"""
        data = await self.db.fetch_one(query, {"name": name, "user_id": user_id})
        return CodeFlowMapper.from_record_(data)


def get_code_flow_repository(db: Database = Depends(get_database)) -> CodeFlowRepository:
    return CodeFlowRepository(db)
