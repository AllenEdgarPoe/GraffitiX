import json
import uuid
import redis
import threading
import time

from logger_setup import LogType, set_logger


class Redis():
    def __init__(self, args):
        self.app_close = None
        self.redis_status = False
        try:
            set_logger(LogType.LT_INFO, 'Init RedisWorker')
            self.set_app_status(False)

            self.host = args.redis_host
            self.port = args.redis_port
            # self.pwd = args.redis_pwd
            self.redis_conn_delay = args.redis_conn_delay

            self.connection_pool = redis.ConnectionPool(host=self.host,
                                                        # password=self.pwd,
                                                        port=self.port,
                                                        socket_keepalive=True,
                                                        socket_timeout=500,
                                                        db=0)
            # self.event_callback = None
            # self.redis_conn = redis.Redis(connection_pool=self.connection_pool)

            self.redisThread = threading.Thread(target=self.run, daemon=False)
            self.redisThread.start()

        except Exception as e:
            set_logger(LogType.LT_EXCEPTION, str(e))

    def set_app_status(self, status: bool):
        self.app_close = status

    def get_app_status(self):
        return self.app_close

    def set_redis_status(self, status: bool):
        self.redis_status = status

    def get_redis_status(self):
        return self.redis_status

    def is_redis_available(self):
        try:
            if self.redis_conn != None:
                self.redis_conn.ping()
                self.set_redis_status(True)
                return True
            else:
                self.set_redis_status(False)
                return False
        except Exception as e:
            self.set_redis_status(False)
            return False
        finally:
            time.sleep(1)

    def store_data(self, json_message):
        try:
            key_name = "GraffitiX:output_queue"  # 저장할 List 키
            self.redis_conn.lpush(key_name, json.dumps(json_message))
            set_logger(LogType.LT_INFO, f'[Redis] Store : {json_message["id"]}')

        except Exception as e:
            set_logger(LogType.LT_EXCEPTION, f'[Redis] Store Error: {str(e)}')

    def pop_oldest_data(self):
        try:
            key_name = "GraffitiX:input_queue"
            data_str = self.redis_conn.rpop(key_name)
            if data_str:
                data_dict = json.loads(data_str)
                set_logger(LogType.LT_INFO, f'[Redis] Get : {data_dict["id"]}')
                return data_dict

        except Exception as e:
            set_logger(LogType.LT_EXCEPTION, f'[Redis] Get Error: {str(e)}')


    def run(self):
        try:
            """ redis command """
            """ https://redis.io/docs/latest/develop/connect/clients/python/ """
            """ https://redis-py.readthedocs.io/en/stable/commands.html """

            local_tick = time.perf_counter()

            while self.get_app_status() != True:
                try:
                    if self.is_redis_available():
                        # set_logger(LogType.LT_INFO, '[Redis] Redis Connection Good')
                        pass
                    else:
                        current_tick = time.perf_counter()
                        if current_tick - local_tick >= self.redis_conn_delay:
                            set_logger(LogType.LT_WARNING, '[Redis] Redis Connection Failed. Reconnect...')
                            self.redis_conn = redis.Redis(connection_pool=self.connection_pool)
                            if self.redis_conn!=None:
                                set_logger(LogType.LT_WARNING, '[Redis] Redis Connected')
                            local_tick = current_tick
                except:
                    pass

                time.sleep(1)

        except:
            set_logger(LogType.LT_EXCEPTION, 'Exception')

    def close(self):
        try:
            self.set_app_status(True)

            if self.redisThread != None:
                self.redisThread.join()
                self.redisThread = None

            set_logger(LogType.LT_INFO, 'Close RedisWorker')
        except:
            set_logger(LogType.LT_EXCEPTION, 'Exception')


if __name__ == "__main__":
    from cmd_args import parse_args
    args = parse_args()
    redis = Redis(args)
