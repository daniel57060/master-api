import c_inspectors
import uuid

from fastapi import Depends, UploadFile
from pathlib import Path

from ..exceptions import AlreadyExistsError, DomainError, UnexpectedError
from ..jobs.process_code_flow_job import ProcessCodeFlowJob, get_process_code_flow_job
from ..models import CodeFlowModel, UserModel
from ..repositories.code_flow_repository import CodeFlowInsert, CodeFlowRepository, get_code_flow_repository
from ..resources import Resources


class StoreCodeFlowUseCase:
    def __init__(self, repository: CodeFlowRepository, job: ProcessCodeFlowJob) -> None:
        self.repository = repository
        self.job = job

    async def execute(self, author: UserModel, code_file: UploadFile) -> CodeFlowModel:
        code_path = Path(code_file.filename)

        if code_path.suffix != '.c':
            raise DomainError(
                f"Invalid file extension: {code_path.suffix} (expected .c)")

        data = await self.repository.get_by_name(code_file.filename)
        if data is not None:
            raise AlreadyExistsError(f"CodeFlow with name {code_file.filename} already exists")

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
            raise DomainError(f"Error processing file: {e}")

        try:
            code_flow_id = await self.repository.insert(CodeFlowInsert(
                name=code_file.filename,
                file_id=file_id,
                user_id=author.id,
            ))

            result = await self.repository.get_by_id(code_flow_id)
            if result is None:
                raise UnexpectedError("CodeFlow is None after insert")
            self.job.create_job(result)
            return result
        except Exception as e:
            if input_path.exists():
                input_path.unlink()
            if output_path.exists():
                output_path.unlink()
            raise DomainError(f"Error storing file: {e}")


def get_store_code_flow_use_case(
    repository: CodeFlowRepository = Depends(get_code_flow_repository),
    job: ProcessCodeFlowJob = Depends(get_process_code_flow_job)
) -> StoreCodeFlowUseCase:
    return StoreCodeFlowUseCase(repository, job)
