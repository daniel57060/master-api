import uuid
import c_inspectors

from pathlib import Path
from fastapi import Depends, UploadFile

from server.jobs.process_code_flow_job import ProcessCodeFlowJob, get_process_code_flow_job


from ..exceptions import AlreadyExistsError, DomainError
from ..resources import Resources
from ..models import CodeFlowModel
from ..services.code_flow_service import CodeFlowService, CodeFlowStore, get_code_flow_service


class StoreCodeFlowUseCase:
    def __init__(self, service: CodeFlowService, job: ProcessCodeFlowJob) -> None:
        self.service = service
        self.job = job

    async def execute(self, code_file: UploadFile) -> CodeFlowModel:
        code_path = Path(code_file.filename)

        if code_path.suffix != '.c':
            raise DomainError(
                f"Invalid file extension: {code_path.suffix} (expected .c)")

        code_flow = await self.service.code_flow_index(name=code_file.filename)
        if code_flow:
            raise AlreadyExistsError(
                f"CodeFlow with name {code_file.filename} already exists")

        file_id = uuid.uuid4().hex
        input_path = Resources.FILES / f"{file_id}_o.c"
        output_path = Resources.FILES / f"{file_id}_t.c"

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

        try:
            result = await self.service.code_flow_store(CodeFlowStore(
                name=code_file.filename,
                file_id=file_id,
            ))

            self.job.create_job(result)
            return result
        except Exception as e:
            if input_path.exists():
                input_path.unlink()
            if output_path.exists():
                output_path.unlink()
            raise e


def get_store_code_flow_use_case(
    service: CodeFlowService = Depends(get_code_flow_service),
    job: ProcessCodeFlowJob = Depends(get_process_code_flow_job)
):
    yield StoreCodeFlowUseCase(service=service, job=job)
