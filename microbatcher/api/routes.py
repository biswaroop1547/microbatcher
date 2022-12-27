import asyncio
import traceback
from time import sleep, time

from fastapi.concurrency import run_in_threadpool
from loguru import logger

import microbatcher.constants as const
from microbatcher.api import app, handlers
from microbatcher.api.models import errors, requests, responses
from microbatcher.types import DataPoint, ProcessorQueue

PROCESSOR = handlers.Processor()


@app.post("/predict/")
async def predict(payload: requests.Input):
    datapoint = DataPoint(payload.dict().get("data"))
    pred = await PROCESSOR.inference(datapoint)

    return {"message": "ok", "result": pred}
