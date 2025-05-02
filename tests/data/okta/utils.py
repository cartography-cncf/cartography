import time

from requests import Response


def create_response():
    response = Response()
    response.headers["x-rate-limit-limit"] = "300"
    response.headers["x-rate-limit-remaining"] = "299"
    response.headers["x-rate-limit-reset"] = str(int(time.time()) + 59)
    return response


def create_throttled_response():
    response = Response()
    response.headers["x-rate-limit-limit"] = "300"
    response.headers["x-rate-limit-remaining"] = "3"
    response.headers["x-rate-limit-reset"] = str(int(time.time()) + 3)
    return response


def create_long_timeout_response():
    response = Response()
    response.headers["x-rate-limit-limit"] = "300"
    response.headers["x-rate-limit-remaining"] = "3"
    response.headers["x-rate-limit-reset"] = str(int(time.time()) + 120)
    return response
