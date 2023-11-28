import asyncio
import logging
from pathlib import Path
import requests
from typing import List


from fastapi import Depends

from server.services.code_flow_service import CodeFlowService, CodeFlowUpdate, get_code_flow_service

from ..resources import Resources
from ..models import CodeFlowModel
from ..env import env

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
        await self.service.code_flow_processed(data.id, str(e))

    async def process(self, data: CodeFlowModel):
        flow_path = Path(data.flow_path).name
        cmd = ['sh', './run.sh', flow_path]
        self.logger.info(f"Processing {data.name}")
        try:
            result = requests.post(f'{env.c_runner_url}/v1/run', json={
                "cmd": cmd,
                "timeout": 10,
            })
            if result.status_code != 200:
                await self._update_flow_error(data, result)
                return

            result = result.json()
            if result["error"] is not None:
                await self._update_flow_error(data, f"""ERROR: {result["error"]}""")
                return

            if result['ok']['returncode'] != 0:
                await self._update_flow_error(data, f"""OK ERROR: STDOUT:\n{result['ok']['stdout']}\nSTDERR:\n{result['ok']['stderr']}""")
                return

            if not (Resources.FILES / flow_path).exists():
                await self._update_flow_error(data, f"EXTERNAL: Flow file not generated")
                return

        except requests.exceptions.RequestException as e:
            await self._update_flow_error(data, f"REQUEST: {e}")
            return

        self.logger.info(f"Complete {data.name}")
        await self.service.code_flow_processed(data.id)

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
    data = await service.code_flow_unprocessed()
    for item in data:
        job.create_job(item)
    yield job
