from time import sleep, time

import microbatcher.constants as const
from microbatcher.api import app, loaders
from microbatcher.api.models import errors, requests, responses
from microbatcher.types import DataPoint, ProcessorQueue

global_queue = ProcessorQueue(maxsize=const.QUEUE_MAXSIZE)

loadedModel = loaders.Model()
global_queue.set_model(loadedModel)


@app.post("/predict/")
def read_root(payload: requests.Input):
    datapoint = DataPoint(payload.dict().get("data"))

    while global_queue.put(datapoint) is False:
        # print(f"queue to empty -> curr size : {global_queue.item_count}")
        sleep(0.0000001)
        pass

    while (
        global_queue.start
        and ((time_passed := (time() - global_queue.start)) < 1.2)
        and (global_queue.item_count <= const.QUEUE_MAXSIZE)
    ):
        sleep(0.0000001)
        pass

    run_success = global_queue.process_items()

    while True:
        pred = global_queue.get_prediction(datapoint.uuid)
        if pred is not None:
            break

        print("waiting for prediction:", datapoint.data, pred)
        print("results inside loop:", global_queue.results)
        # print("run_status:", run_success)
        sleep(0.0000001)
        pass
    print("predddd:", pred)
    return {"message": "ok", "result": pred}
