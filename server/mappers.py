from databases.interfaces import Record
from typing import List
from server.models import CodeFlowModel, CodeFlowShow


class CodeFlowShowMapper:
    @staticmethod
    def from_model(model: CodeFlowModel) -> CodeFlowShow:
        return CodeFlowShow(
            id=model.id,
            name=model.name,
            code_path=model.code_path,
            transform_path=model.transform_path,
            flow_path=model.flow_path,
            processed=model.processed,
            user_id=model.user_id,
            private=model.private,
            flow_error=model.flow_error,
            input=model.input
        )
    
    @staticmethod
    def from_all_models(models: List[CodeFlowModel]) -> List[CodeFlowShow]:
        return [CodeFlowShowMapper.from_model(model) for model in models]


class CodeFlowMapper:
    @staticmethod
    def from_record(record: Record) -> CodeFlowModel:
        return CodeFlowModel(**dict(record))

    @staticmethod
    def from_record_(record: Record | None) -> CodeFlowModel | None:
        if record is None:
            return None
        return CodeFlowMapper.from_record(record)
    
    @staticmethod
    def from_all_records(records: List[Record]) -> List[CodeFlowModel]:
        return [CodeFlowMapper.from_record(record) for record in records]
