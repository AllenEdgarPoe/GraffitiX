import sys
import signal
import threading
import time

import cmd_args
from logger_setup import LogType, set_logger, init_logger
from utils import preparation

from WSClientWorker import WebSocketClient
from RedisWorker import Redis
from AIContentWorker import AIContent

class MainWorker():
    def __init__(self):
        self.redis = None

        try:
            set_logger(LogType.LT_INFO, 'Init MainWorker')
            signal.signal(signal.SIGINT, self.signal_handler)

            self.args = cmd_args.parse_args()
            preparation(self.args)

            self.running = True

            self.redis = Redis(self.args)
            self.wsclient = WebSocketClient(self.args)
            self.content = AIContent(self.args)
            self.register_content_callbacks()

            time.sleep(10)

            self.getThread = threading.Thread(target=self._get_redis_data, daemon=True)
            self.getThread.start()


            while self.running:
                time.sleep(0.001)

            self.getThread.join()

            if self.redis != None:
                self.redis.close()
                self.redis = None

            set_logger(LogType.LT_INFO, 'Close MainWorker')


        except Exception as e:
            set_logger(LogType.LT_EXCEPTION, f"Exception: {e}")

    def signal_handler(self, sig, frame):
        self.running = False

    def redis_ping_callback(self):
        return self.redis.is_redis_available()

    def store_redis_data_callback(self, data):
        return self.redis.store_data(data)

    def que_and_rcv_data_callback(self, data):
        prompt, timeout = data[0], data[1]
        return self.wsclient.que_and_rcv_data(prompt, timeout)

    def register_content_callbacks(self):
        self.content.set_callbacks(
            self.que_and_rcv_data_callback,
            self.store_redis_data_callback
        )

    def _get_redis_data(self):
        while self.running:
            try:
                data = self.redis.pop_oldest_data()
                if data:
                    self.content.run(data, timeout=10)
                time.sleep(1)
            except Exception as e:
                pass


def main():
    init_logger()
    set_logger(LogType.LT_INFO, "+-----------------------------------+")
    set_logger(LogType.LT_INFO, "+         Start Graffiti X    +")
    set_logger(LogType.LT_INFO, "+-----------------------------------+")
    try:
        mainworker = MainWorker()

    except:
        set_logger(LogType.LT_EXCEPTION, 'Exception')
    finally:
        set_logger(LogType.LT_INFO, "+-----------------------------------+")
        set_logger(LogType.LT_INFO, "+         End Graffiti X     +")
        set_logger(LogType.LT_INFO, "+-----------------------------------+")

        sys.exit()

if __name__ == "__main__":
    main()



