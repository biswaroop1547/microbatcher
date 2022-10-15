import uuid
from typing import Any, Union

import numpy as np


class DataPoint:
    def __init__(self, data: Union[Any, None]):  # TODO: fix type
        self.data = np.array(data)
        self.uuid = str(uuid.uuid4())
        self.processed = False

    def data_processed(self):
        self.processed = True
