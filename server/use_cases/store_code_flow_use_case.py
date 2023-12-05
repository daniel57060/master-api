import c_inspectors
import uuid

from fastapi import Depends, UploadFile
from pathlib import Path

from ..exceptions import AlreadyExistsError, DomainError, UnexpectedError
from ..jobs.process_code_flow_job import ProcessCodeFlowJob, get_process_code_flow_job
from ..mappers import CodeFlowShowMapper
from ..models import CodeFlowShow, UserModel
from ..repositories.code_flow_repository import CodeFlowInsert, CodeFlowRepository, get_code_flow_repository
from ..resources import Resources

# TODO: https://www.slingacademy.com/article/how-to-run-background-tasks-in-fastapi/#:~:text=Define%20your%20task%20functions%20using%20the%20%40celery.task%20decorator%2C,terminals%20or%20processes%2C%20using%20the%20celery%20worker%20command.

class StoreCodeFlowUseCase:
    def __init__(self, repository: CodeFlowRepository, job: ProcessCodeFlowJob) -> None:
        self.repository = repository
        self.job = job

    async def execute(self, author: UserModel, code_file: UploadFile) -> CodeFlowShow:
        if code_file.filename is None:
            raise DomainError("Filename is None")

        code_path = Path(code_file.filename)

        if code_path.suffix != '.c':
            raise DomainError(
                f"Invalid file extension: {code_path.suffix} (expected .c)")

        data = await self.repository.get_by_user_id_and_name(author.id, code_file.filename)
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

            data = await self.repository.get_by_id(code_flow_id)
            if data is None:
                raise UnexpectedError("CodeFlow is None after insert")
            return CodeFlowShowMapper.from_model(data)
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
