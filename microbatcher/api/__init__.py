from multiprocessing import Semaphore

from fastapi import FastAPI

import microbatcher.constants as const
from microbatcher.api import handlers

app = FastAPI()


@app.on_event("startup")
async def startup():
    print("starting server")


@app.on_event("shutdown")
async def cleanup():
    print("cleaning resources & shutting down server")
    Semaphore().release()
