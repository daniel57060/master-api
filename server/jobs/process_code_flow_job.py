import asyncio
import logging
import requests

from fastapi import BackgroundTasks, Depends
from pathlib import Path
from typing import Any, Optional

from ..env import env
from ..models import CodeFlowModel
from ..repositories.code_flow_repository import CodeFlowRepository, get_code_flow_repository
from ..resources import Resources


CodeFlowQueue = asyncio.Queue[CodeFlowModel]


class ProcessCodeFlowJob:
    def __init__(self, repository: CodeFlowRepository, queue: CodeFlowQueue):
        self.repository = repository
        self.logger = logging.getLogger(__name__)
        self.queue = queue
        self.logger.info("ProcessCodeFlowJob initialized")

    def create_job(self, data: CodeFlowModel) -> None:
        self.logger.info(f"Creating job for {data.name}")
        self.queue.put_nowait(data)

    async def _update_flow_error(self, data: CodeFlowModel, e: Any) -> None:
        self.logger.error(f"Error processing {data.name}: {e}")
        await self.repository.update_processed(data.id, str(e))

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

            if result is None:
                await self._update_flow_error(data, f"""ERROR: 'result' is None""")
                return

            if result["ok"] is None and result["error"] is None:
                await self._update_flow_error(data, f"""ERROR: 'result["ok"]' is None and result["error"] is None""")
                return

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
        await self.repository.update_processed(data.id)
    
    async def run(self) -> None:
        while True:
            data = await self.queue.get()
            try:
                await self.process(data)
            except Exception as e:
                self.logger.error(f"Unknown error {data.name}: {e}")
            self.queue.task_done()


class ProcessCodeFlowJobSingleton:
    instance: Optional[ProcessCodeFlowJob] = None

    async def get_instance(self, repository: CodeFlowRepository, background_tasks: BackgroundTasks) -> ProcessCodeFlowJob:
        if ProcessCodeFlowJobSingleton.instance is not None:
            return ProcessCodeFlowJobSingleton.instance
        # First
        queue: CodeFlowQueue = asyncio.Queue()
        job = ProcessCodeFlowJob(repository, queue)
        background_tasks.add_task(job.run)
        data = await job.repository.get_all_unprocessed_and_failed()
        for item in data:
            job.create_job(item)
        ProcessCodeFlowJobSingleton.instance = job
        return ProcessCodeFlowJobSingleton.instance


async def get_process_code_flow_job(
    background_tasks: BackgroundTasks,
    code_flow_repository: CodeFlowRepository = Depends(get_code_flow_repository),
) -> ProcessCodeFlowJob:
    return await ProcessCodeFlowJobSingleton().get_instance(code_flow_repository, background_tasks)
