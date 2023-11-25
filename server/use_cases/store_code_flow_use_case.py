import uuid
import c_inspectors

from pathlib import Path
from fastapi import Depends, UploadFile

from ..exceptions import DomainError
from ..jobs.process_code_flow_job import ProcessCodeFlowJob, get_process_code_flow_job
from ..models import CodeFlowModel, UserModel
from ..resources import Resources
from ..services.code_flow_service import CodeFlowService, CodeFlowStore, get_code_flow_service


class StoreCodeFlowUseCase:
    def __init__(self, service: CodeFlowService, job: ProcessCodeFlowJob) -> None:
        self.service = service
        self.job = job

    async def execute(self, author: UserModel, code_file: UploadFile) -> CodeFlowModel:
        code_path = Path(code_file.filename)

        if code_path.suffix != '.c':
            raise DomainError(
                f"Invalid file extension: {code_path.suffix} (expected .c)")

        await self.service.code_flow_for_store(code_file.filename)

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
            return DomainError(f"Error processing file: {e}")

        try:
            code_flow_id = await self.service.code_flow_store(CodeFlowStore(
                name=code_file.filename,
                file_id=file_id,
                user_id=author.id,
            ))

            result = await self.service.code_flow_show(code_flow_id, author)
            self.job.create_job(result)
            return result
        except Exception as e:
            if input_path.exists():
                input_path.unlink()
            if output_path.exists():
                output_path.unlink()
            raise DomainError(f"Error storing file: {e}")


def get_store_code_flow_use_case(
    service: CodeFlowService = Depends(get_code_flow_service),
    job: ProcessCodeFlowJob = Depends(get_process_code_flow_job)
):
    yield StoreCodeFlowUseCase(service=service, job=job)
