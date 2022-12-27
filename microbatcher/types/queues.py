import asyncio
import multiprocessing
import threading
from multiprocessing.queues import Queue
from time import sleep, time
from typing import Optional

import numpy as np

import microbatcher.constants as const
from microbatcher.api.handlers.loaders import Model


class MicroQueue(Queue):
    def __init__(self, maxsize=0, *args, ctx=None, **kwargs):
        super().__init__(maxsize, *args, ctx=multiprocessing.get_context())

    def __iter__(self):
        return self

    def __next__(self):
        if self.empty():
            raise StopIteration
        return self.get()


class ProcessorQueue:
    def __init__(self, maxsize=const.QUEUE_MAXSIZE, timeout=const.QUEUE_TIMEOUT):
        self.queue = MicroQueue()
        self.max_queue_size = maxsize
        self.timeout = timeout
        self.mutex = threading.Lock()
        self.tasks_processing = threading.Condition(self.mutex)
        self.task_enqueue = threading.Condition(self.mutex)
        self.model: Optional[Model] = None
        self.processed_outputs = {}
        self.results = []
        self.start = 0
        self.item_count = 0
        self.is_done = {}

    async def patience_timeout(self):
        return (
            not self.start
            or ((time() - self.start) >= self.timeout)
            or (self.item_count > self.max_queue_size)
        )

    async def put(self, obj):
        queue_space_available = False
        try:
            self.mutex.acquire()

            if self.item_count < self.max_queue_size:
                self.queue.put(obj)
                self.item_count += 1
                print(f"item count: {self.item_count}")
                self.start_time()
                queue_space_available = True
        finally:
            self.mutex.release()
        return queue_space_available

    def start_time(self):
        if self.item_count == 1:
            self.start = time()

    def reset_processed(self):
        self.processed_outputs = {}
        self.results = []

    def reset_time(self, datapoints_processed):
        self.start = 0
        self.item_count -= datapoints_processed

    def set_model(self, model):
        self.model = model

    def __iter__(self):
        return self

    def __next__(self):
        if self.queue.empty():
            raise StopIteration
        return self.queue.get()

    def all_processes_done(self):
        return not self.is_done or all(list(self.is_done.values()))

    async def get_prediction(self, uuid):
        pred = None
        try:
            if pred := self.processed_outputs.get(uuid):
                self.is_done[uuid] = True
        finally:
            return pred

    def process_items(self):
        run_success = False
        with self.mutex:
            try:
                if (
                    (model := self.model)
                    and not self.queue.empty()
                    and self.all_processes_done()
                ):
                    # process items in queue
                    datapoints = []
                    uuids = []
                    self.reset_processed()
                    for idx, datapoint in enumerate(self.queue):
                        datapoints.append(datapoint.data)
                        uuids.append(datapoint.uuid)

                    self.results = model.predict(np.array(datapoints, dtype=object))
                    self.processed_outputs = {
                        uuids[idx]: res.tolist()
                        for idx, res in enumerate(self.results)  # noqa: E501
                    }
                    self.is_done = {
                        uuids[idx]: False for idx in range(len(self.results))
                    }
                    self.reset_time(datapoints_processed=len(self.results))
                    run_success = True
            finally:
                return run_success
