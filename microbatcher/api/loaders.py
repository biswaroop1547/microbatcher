from multiprocessing import Queue
from time import sleep, time
from typing import List

import numpy as np
from loguru import logger


def time_it(func):  # TODO: turn this into utils or something
    def wrapper(*args, **kwargs):
        start = time()
        res = func(*args, **kwargs)
        end = time()
        logger.info(f"\n{func.__name__} took {end - start} seconds")
        return res

    return wrapper


class Model:
    def __init__(self, max_queue_size=1):
        logger.info("FakeModel.__init__")
        sleep(1)
        self.max_queue_size = max_queue_size
        self.queue = Queue(maxsize=max_queue_size)
        logger.info("FakeModel.__init__ done")

    @time_it
    def predict(self, datapoints: np.ndarray) -> np.ndarray:
        logger.info("FakeModel.predict")
        for i in range(18000000):
            i * i
        return datapoints * 2


def cpu_intensive_process(queue: Queue):
    """
    A CPU-intensive process.
    """
    if queue.qsize() > 5:
        logger.info("Starting CPU-intensive process")
        start = time()
        for i in range(18000000):
            i * i
        logger.info("Finished CPU-intensive process")
        end = time()
        logger.info(
            "CPU-intensive process took {} seconds".format(end - start)
        )  # noqa: E501
        queue.get()
