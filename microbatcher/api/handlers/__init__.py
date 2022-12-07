import asyncio

from fastapi.concurrency import run_in_threadpool
from loguru import logger

import microbatcher.constants as const
from microbatcher.api.handlers import loaders, wrappers
from microbatcher.types import DataPoint, ProcessorQueue


class Processor:
    def __init__(self, queue_max_size=const.QUEUE_MAXSIZE, **kwargs):
        self.queue = ProcessorQueue(maxsize=queue_max_size)
        self.model = loaders.Model()
        self.queue.set_model(self.model)

    async def process(self):
        _ = await run_in_threadpool(self.queue.process_items)

    @wrappers.retry_on_timeout
    async def get_response(self, datapoint: DataPoint):
        # Wait for the prediction to be available
        pred = await asyncio.wait_for(
            self.queue.get_prediction(datapoint.uuid), timeout=const.OPS_TIMEOUT
        )
        return pred

    @wrappers.retry_on_timeout
    async def enqueue_request(self, datapoint: DataPoint):
        # Wait for the queue to be ready to accept items
        while True:
            if await asyncio.wait_for(
                self.queue.put(datapoint), timeout=const.OPS_TIMEOUT
            ):
                return

    @wrappers.retry_on_timeout
    async def queue_patience_timeout(self):
        # Wait for the queue to fill up/timeout to start processing
        while True:
            if await asyncio.wait_for(
                self.queue.patience_timeout(), timeout=const.OPS_TIMEOUT
            ):
                return
