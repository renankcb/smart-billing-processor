import time
from loguru import logger

def log_execution_time(func):
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        elapsed_time = time.perf_counter() - start_time
        logger.info(f"Execution time for {func.__name__}: {elapsed_time:.2f} seconds.")
        return result
    return wrapper
