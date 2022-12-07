import asyncio
import traceback
from time import sleep, time

from fastapi.concurrency import run_in_threadpool
from loguru import logger

import microbatcher.constants as const
from microbatcher.api import app, loaders
from microbatcher.api.models import errors, requests, responses
from microbatcher.types import DataPoint, ProcessorQueue

global_queue = ProcessorQueue(maxsize=const.QUEUE_MAXSIZE)

loadedModel = loaders.Model()
global_queue.set_model(loadedModel)


async def get_response(queue, datapoint):
    # Wait for the prediction to be available
    while True:
        try:
            if pred := await asyncio.wait_for(
                queue.get_prediction(datapoint.uuid), timeout=const.OPS_TIMEOUT
            ):
                return pred
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout happened while trying to fetch response\n{e}")


async def enqueue_request(queue, datapoint):
    # Wait for the queue to be ready to accept items
    while True:
        try:
            if await asyncio.wait_for(queue.put(datapoint), timeout=const.OPS_TIMEOUT):
                return
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout happened while enqueuing request\n{e}")


async def queue_patience_timeout(queue):
    # Wait for the queue to fill up/timeout to start processing
    while True:
        try:
            if await asyncio.wait_for(
                queue.patience_timeout(), timeout=const.OPS_TIMEOUT
            ):
                return
        except asyncio.TimeoutError as e:
            logger.error(
                f"Timeout happened while checking if queue is filled up\n{traceback.format_exc()}"
            )


@app.post("/predict/")
async def predict(payload: requests.Input):
    datapoint = DataPoint(payload.dict().get("data"))
    await enqueue_request(global_queue, datapoint)
    await queue_patience_timeout(global_queue)
    run_success = await run_in_threadpool(global_queue.process_items)
    pred = await get_response(global_queue, datapoint)

    return {"message": "ok", "result": pred}
