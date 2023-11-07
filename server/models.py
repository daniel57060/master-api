from pydantic import BaseModel


class CodeFlowModel(BaseModel):
    id: int
    name: str
    code_path: str
    flow_path: str


class CodeFlowShow(BaseModel):
    id: int
    name: str

    class Config():
        from_attributes = True
