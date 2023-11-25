import asyncio
import logging
import requests
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
        self.logger = logging.getLogger(__name__)

    def create_job(self, data: CodeFlowModel):
        self.queue.put_nowait(data)

    async def _update_flow_error(self, data: CodeFlowModel, e):
        self.logger.error(f"Error processing {data.name}")
        error = str(e)
        await self.service.code_flow_update(data.id, flow_error=error, processed=True)

    async def process(self, data: CodeFlowModel):
        filename = f"{data.file_id}_t.c"
        cmd = ['sh', '-c', f'./run.sh {filename}']
        self.logger.info(f"Processing {data.name}")
        try:
            result = requests.post('http://c-runner:80/v1/run', json={
                "cmd": cmd,
                "timeout": 10,
            })
            if result.status_code != 200:
                await self._update_flow_error(data, result)
                return
        except requests.exceptions.RequestException as e:
            await self._update_flow_error(data, e)
            return
        self.logger.info(f"Complete {data.name}")
        await self.service.code_flow_update(data.id, processed=True, flow_error=None)

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
