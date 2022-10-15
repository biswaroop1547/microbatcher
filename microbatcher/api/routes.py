import asyncio
from time import sleep, time

from fastapi.concurrency import run_in_threadpool

import microbatcher.constants as const
from microbatcher.api import app, loaders
from microbatcher.api.models import errors, requests, responses
from microbatcher.types import DataPoint, ProcessorQueue

global_queue = ProcessorQueue(maxsize=const.QUEUE_MAXSIZE)

loadedModel = loaders.Model()
global_queue.set_model(loadedModel)


async def get_response(queue_, datapoint):
    while not (pred := queue_.get_prediction(datapoint.uuid)):
        await asyncio.sleep(0.0000001)
    return pred


async def enqueue_request(queue_, datapoint):
    while global_queue.put(datapoint) is False:
        await asyncio.sleep(0.0000001)


async def queue_patience_timeout(queue_):
    while (
        queue_.start
        and ((time() - queue_.start) < const.QUEUE_TIMEOUT)
        and (queue_.item_count <= const.QUEUE_MAXSIZE)
    ):
        await asyncio.sleep(0.0000001)


@app.post("/predict/")
async def read_root(payload: requests.Input):
    datapoint = DataPoint(payload.dict().get("data"))
    await enqueue_request(global_queue, datapoint)
    await queue_patience_timeout(global_queue)
    run_success = await run_in_threadpool(global_queue.process_items)
    pred = await get_response(global_queue, datapoint)

    return {"message": "ok", "result": pred}
