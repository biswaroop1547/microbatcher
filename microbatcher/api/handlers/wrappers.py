import asyncio
from functools import wraps
from time import time

from loguru import logger

import microbatcher.constants as const


def time_it(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time()
        res = func(*args, **kwargs)
        end = time()
        logger.info(f"\n{func.__name__} took {end - start} seconds")
        return res

    return wrapper


def retry_on_timeout(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        attempts = 0
        while True:
            try:
                return await func(*args, **kwargs)
            except asyncio.TimeoutError as e:
                attempts += 1
                if attempts >= const.MAX_ATTEMPTS:
                    # Handle failure to receive a response after the maximum number of attempts
                    logger.error(
                        f"Failed to receive response after {const.MAX_ATTEMPTS} attempts\n{e}"
                    )
                    return None
                logger.error(
                    f"Timeout happened while trying to fetch response (attempt {attempts})\n{e}"
                )

    return wrapper
