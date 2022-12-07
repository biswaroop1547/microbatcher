from multiprocessing import Queue
from time import sleep, time
from typing import List

import numpy as np
from loguru import logger

from microbatcher.api.handlers import wrappers


class Model:
    def __init__(self):
        logger.info("FakeModel.__init__")
        sleep(1)
        logger.info("FakeModel.__init__ done")

    @wrappers.time_it
    def predict(self, datapoints: np.ndarray) -> np.ndarray:
        logger.info("FakeModel.predict")
        for i in range(18000000):
            i * i
        return datapoints * 2
