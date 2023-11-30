from typing import Optional
from pydantic import BaseModel


class CodeFlowModel(BaseModel):
    id: int
    name: str
    file_id: str
    processed: bool
    user_id: int
    private: bool
    flow_error: Optional[str]

    @property
    def code_path(self):
        return f'/static/files/{self.file_id}_o.c'

    @property
    def transform_path(self):
        return f'/static/files/{self.file_id}_t.c'

    @property
    def flow_path(self):
        return f'/static/files/{self.file_id}_t.json'


class CodeFlowShow(BaseModel):
    id: int
    name: str
    code_path: str
    flow_path: str
    processed: bool
    user_id: int
    private: bool
    flow_error: Optional[str]

    class Config():
        from_attributes = True


class UserModel(BaseModel):
    id: int
    username: str
    password: str
    version: int = 0

    def redact(self):
        self.password = "[REDACTED]"
        return self
