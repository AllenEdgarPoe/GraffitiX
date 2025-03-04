import os
import time
import threading
from queue import Queue
from loguru import logger
from enum import Enum

cs_lock = threading.Lock()
log_queue = Queue()

# constant
class LogType(Enum):
    LT_INFO      = 1
    LT_EXCEPTION = 2
    LT_ERROR     = 3
    LT_WARNING = 4


def set_log_queue(data: str):
    try:
        if log_queue != None:
            log_queue.put(data)
    except Exception as e:
        print(e)
        pass

def get_log_queue():
    try:
        if log_queue != None:
            return log_queue.get()
    except Exception as e:
        print(e)
        pass

def get_log_size():
    try:
        if log_queue != None:
            return log_queue.qsize()
    except Exception as e:
        print(e)
        pass

    return 0

def set_logger(type: LogType | None, data: str):
    try:
        with cs_lock:
            now = time
            if type == LogType.LT_INFO:
                set_log_queue('<color=white>'+ now.strftime('%Y-%m-%d %H:%M:%S ')+ data +'</white><br>')
                logger.info(data)
            if type == LogType.LT_EXCEPTION:
                set_log_queue('<color=green>'+ now.strftime('%Y-%m-%d %H:%M:%S ')+ data +'</green><br>')
                logger.exception(data)
            if type == LogType.LT_ERROR:
                set_log_queue('<color=red>'+ now.strftime('%Y-%m-%d %H:%M:%S ')+ data +'</red><br>')
                logger.error(data)
            if type == LogType.LT_WARNING:
                set_log_queue('<color=blue>'+ now.strftime('%Y-%m-%d %H:%M:%S ')+ data +'</blue><br>')
                logger.warning(data)
    except Exception as e:
        print(e)
        pass

def init_logger():
    try:
        if not os.path.exists(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'log')):
            os.makedirs(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'log'), exist_ok=True)

        file_name = time.strftime('%Y-%m-%d')+'.log'
        logger.add(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'log', file_name), format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", rotation="1MB")
    except Exception as e:
        print(e)
        pass

if __name__ == "__main__":
    init_logger()
    set_logger(LogType.LT_INFO, 'this is info')
    set_logger(LogType.LT_EXCEPTION, 'this is exception')
    set_logger(LogType.LT_ERROR, 'this is error')
    print(get_log_queue())


