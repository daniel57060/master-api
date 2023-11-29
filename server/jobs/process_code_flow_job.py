import asyncio
import logging
import requests

from fastapi import Depends
from pathlib import Path
from typing import Any

from ..env import env
from ..models import CodeFlowModel
from ..resources import Resources
from ..services.code_flow_service import CodeFlowService, get_code_flow_service


CODE_FLOW_QUEUE: asyncio.Queue[CodeFlowModel] = asyncio.Queue()


class ProcessCodeFlowJob:
    def __init__(self, service: CodeFlowService):
        global CODE_FLOW_QUEUE
        self.queue = CODE_FLOW_QUEUE
        self.service = service
        self.logger = logging.getLogger(__name__)

    def create_job(self, data: CodeFlowModel) -> None:
        self.queue.put_nowait(data)

    async def _update_flow_error(self, data: CodeFlowModel, e: Any) -> None:
        self.logger.error(f"Error processing {data.name}")
        await self.service.code_flow_processed(data.id, str(e))

    async def process(self, data: CodeFlowModel) -> None:
        flow_path = Path(data.flow_path).name
        cmd = ['sh', './run.sh', flow_path]
        self.logger.info(f"Processing {data.name}")
        try:
            response = requests.post(f'{env.c_runner_url}/v1/run', json={
                "cmd": cmd,
                "timeout": 10,
            })
            if response.status_code != 200:
                await self._update_flow_error(data, response)
                return

            result = response.json()
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

    async def run(self):
        while True:
            data = await self.queue.get()
            await self.process(data)
            self.queue.task_done()

    def start(self):
        asyncio.create_task(self.run())


async def get_process_code_flow_job(service: CodeFlowService = Depends(get_code_flow_service)) -> ProcessCodeFlowJob:
    job = ProcessCodeFlowJob(service)
    job.start()
    data = await service.code_flow_unprocessed()
    for item in data:
        job.create_job(item)
    return job
