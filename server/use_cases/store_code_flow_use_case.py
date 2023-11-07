import uuid
import c_inspectors

from pathlib import Path
from fastapi import Depends, UploadFile


from ..exceptions import AlreadyExistsError, DomainError
from ..resources import Resources
from ..models import CodeFlowModel
from ..services.code_flow_service import CodeFlowService, CodeFlowStore, get_code_flow_service


class StoreCodeFlowUseCase:
    def __init__(self, service: CodeFlowService) -> None:
        self.service = service

    async def execute(self, code_file: UploadFile) -> CodeFlowModel:
        code_path = Path(code_file.filename)

        if code_path.suffix != '.c':
            raise DomainError(
                f"Invalid file extension: {code_path.suffix} (expected .c)")

        code_flow = await self.service.code_flow_index(name=code_file.filename)
        if code_flow:
            raise AlreadyExistsError(
                f"CodeFlow with name {code_file.filename} already exists")

        unique_filename = f"{uuid.uuid4()}{Path(code_file.filename).suffix}"
        input_path = Resources.FILES / unique_filename

        unique_filename = f"{uuid.uuid4()}{Path(code_file.filename).suffix}"
        output_path = Resources.FILES / unique_filename

        try:
            with input_path.open("wb") as f:
                f.write(code_file.file.read())
            c_inspectors.ParserAndTransformFile(
                input_path=input_path,
                output_path=output_path,
                json_path=None,
            ).run()
        except Exception as e:
            if input_path.exists():
                input_path.unlink()
            if output_path.exists():
                output_path.unlink()
            return {"error": str(e)}

        result = await self.service.code_flow_store(CodeFlowStore(
            name=code_file.filename,
            code_path=str(input_path),
            flow_path=str(output_path),
        ))

        return result


def get_store_code_flow_use_case(service: CodeFlowService = Depends(get_code_flow_service)):
    yield StoreCodeFlowUseCase(service=service)
