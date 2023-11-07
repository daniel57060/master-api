import asyncio
from pathlib import Path
import subprocess
from typing import List

from fastapi import Depends

from server.services.code_flow_service import CodeFlowService, get_code_flow_service

from ..models import CodeFlowModel

CODE_FLOW_QUEUE: asyncio.Queue[CodeFlowModel] = asyncio.Queue()


class ProcessCodeFlowJob:
    def __init__(self, service: CodeFlowService):
        global CODE_FLOW_QUEUE
        self.queue = CODE_FLOW_QUEUE
        self.service = service

    def create_job(self, data: CodeFlowModel):
        self.queue.put_nowait(data)

    async def _update_flow_error(self, data: CodeFlowModel, e):
        error = '\n'.join(map(str, ['STDERR:', e.stderr, 'STDOUT', e.stdout]))
        await self.service.code_flow_update(
            data.id, flow_error=error, processed=True)

    async def process(self, data: CodeFlowModel):
        filepath = Path(data.transform_path)
        filename = filepath.name
        cmd = ['docker', 'exec', '-it', 'linux-c-dev-tools',
               'sh', '-c', f'./run.sh {filename}']
        try:
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, check=True,
                timeout=10)
            if result.returncode != 0:
                await self._update_flow_error(data, result)
                return
        except subprocess.CalledProcessError as e:
            await self._update_flow_error(data, e)
            return
        await self.service.code_flow_update(data.id, processed=True)

    def get_list(self) -> List[CodeFlowModel]:
        return self.queue._queue

    async def run(self):
        while True:
            data = await self.queue.get()
            await self.process(data)
            self.queue.task_done()

    def start(self):
        asyncio.create_task(self.run())


async def get_process_code_flow_job(service: CodeFlowService = Depends(get_code_flow_service)):
    job = ProcessCodeFlowJob(service)
    job.start()
    data = await service.code_flow_index(processed=False)
    for item in data:
        job.create_job(item)
    yield job
