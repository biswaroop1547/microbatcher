from concurrent import futures
import requests
import os, json
from requests.structures import CaseInsensitiveDict

URL = "http://0.0.0.0:9991/predict/"
HEADERS = CaseInsensitiveDict()
HEADERS["Accept"] = "application/json"
HEADERS["Content-Type"] = "application/json"

tests_json_dir = "test_requests"
file_infos = {}
payloads = []

for json_file in os.listdir(tests_json_dir)*21:
    with open(os.path.join(tests_json_dir, json_file), "r", encoding="utf-8") as f:
        request_dict = json.load(f)
        # file_infos[json_file] = request_dict["true_intent"]
        payload = json.dumps(request_dict, ensure_ascii=False)
        payloads.append(payload.encode("utf-8"))


def wrapper(url, data, workers, retries, pool_maxsize, pool_block):
    session = requests.Session()
    session.mount(
        url,
        requests.adapters.HTTPAdapter(
            max_retries=retries, pool_maxsize=pool_maxsize, pool_block=pool_block
        ),
    )

    def make_request(url, headers, data, req_idx):
        resp = session.post(url, headers=headers, data=data[req_idx])
        # print("STATUS CODE:", resp.status_code, "FILENAME:", list(file_infos)[req_idx])
        return resp

    with futures.ThreadPoolExecutor(workers) as executor:
        request_list = [
            [executor.submit(make_request, url, HEADERS, data, req_idx), req_idx]
            for req_idx in range(len(payloads))
        ]

    all_results = []
    for req, idx in request_list:
        res = req.result().json()
        # pred_intent = res["response"]["intents"][0]["name"]
        # files = list(file_infos)
        # true_intent = file_infos[files[idx]]
        # if pred_intent != true_intent:
            # print(
                # f"FAILED: {files[idx]}\t PREDICTED: {pred_intent} || TRUE: {true_intent}"
            # )
        all_results.append(res)
    return all_results


import time

start_time = time.time()
try:
    r = wrapper(
        url=URL, data=payloads, workers=100, retries=2, pool_maxsize=400, pool_block=False
    )
except Exception as e:
    print(e)
    print("TIME:", time.time() - start_time)
    exit(1)

print("--- %s seconds ---" % (time.time() - start_time))
