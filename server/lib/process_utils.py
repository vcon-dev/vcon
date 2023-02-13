import asyncio
from multiprocessing import Process


def async_runner(func, *args):
    asyncio.run(func(*args))


def start_process(func, *args):
    process = Process(target=func, args=(*args,))
    process.start()
    return process


def start_async_process(func, *args):
    process = Process(target=async_runner, args=(func, *args))
    process.start()
    return process
