import multiprocessing
import threading
from multiprocessing.queues import Queue
from time import time

import numpy as np


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
    def __init__(self, maxsize=999999999):
        self.queue = MicroQueue()
        self.max_queue_size = maxsize
        self.mutex = threading.Lock()
        self.tasks_processing = threading.Condition(self.mutex)
        self.task_enqueue = threading.Condition(self.mutex)
        self.model = None
        self.processed_outputs = {}
        self.results = []
        self.start = 0
        self.item_count = 0
        self.is_done = {}

    def put(self, obj):
        # self.mutex.acquire()
        with self.mutex:
            queue_space_available = False
            try:
                if self.item_count < self.max_queue_size:
                    self.queue.put(obj)
                    self.item_count += 1
                    print(f"item count increased: {self.item_count}")
                    self.start_time()
                    queue_space_available = True
            finally:
                # self.mutex.release()
                return queue_space_available

    def start_time(self):
        if self.item_count == 1:
            print("time initialized")
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

    def get_prediction(self, uuid):
        # print("processed dict", self.processed_outputs)
        # print("results,", self.results)
        pred = None
        # self.mutex.acquire()
        with self.mutex:
            try:
                if pred := self.processed_outputs.get(uuid):
                    self.is_done[uuid] = True
                    print("pred foundddd:", pred)
            finally:
                # self.mutex.release()
                return pred

    def process_items(self):
        run_success = False
        # self.mutex.acquire()
        with self.mutex:
            # acquire lock
            try:
                if (
                    (model := self.model)
                    and not self.queue.empty()
                    and self.all_processes_done()
                ):
                    print("inside processing")
                    # process items in queue
                    datapoints = []
                    uuids = []
                    self.reset_processed()
                    for idx, datapoint in enumerate(self.queue):
                        # self.processed_outputs[datapoint.uuid] = idx
                        datapoints.append(datapoint.data)
                        uuids.append(datapoint.uuid)
                        # datapoint.data_processed()
                    print(f"processingggg {len(datapoints)} datapoints")
                    self.results = model.predict(np.array(datapoints))
                    self.processed_outputs = {
                        uuids[idx]: res.tolist()
                        for idx, res in enumerate(self.results)  # noqa: E501
                    }
                    self.is_done = {
                        uuids[idx]: False for idx in range(len(self.results))
                    }
                    self.reset_time(datapoints_processed=len(self.results))
                    run_success = True
                    print("time resetted")
                    print("count resetted")
                    if len(datapoints) == 1:
                        print("special caseeeeeeeeeeeeeeeee")
                        print(self.processed_outputs, self.results)
                        # exit()
                        # mark those items as processed
            finally:
                # release lock
                # self.mutex.release()
                return run_success
