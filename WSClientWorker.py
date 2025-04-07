import queue
import threading
import time
import websocket
import uuid
from queue import Queue
import json
import urllib.request
import socket
from logger_setup import LogType, set_logger


class WebSocketClient():
    def __init__(self, args):
        set_logger(LogType.LT_INFO, "Init WebSocketClientWorker")
        try:
            self.server_address = args.comfy_host
            self.port = args.comfy_port

            self.client_id = str(uuid.uuid4())

            self.app_close = False
            self.ws_connected = False
            self.recv_queue = Queue()

            self.ws = None

            # self.receiveThread = threading.Thread(target=self.run, daemon=True)
            # self.receiveThread.start()

        except Exception as e:
            set_logger(LogType.LT_EXCEPTION, str(e))

    def set_app_status(self, status: bool):
        self.app_close = status

    def get_app_status(self):
        return self.app_close

    def set_ws_status(self, status: bool):
        self.ws_connected = status

    def get_ws_status(self):
        return self.ws_connected

    def get_client_id(self):
        return self.client_id

    def ws_reconnect(self):
        try:
            self.ws = websocket.WebSocket()
            self.ws.connect(f"ws://{self.server_address}:{self.port}/ws?clientId={self.client_id}", ping_interval=None)
            self.set_ws_status(True)
            set_logger(LogType.LT_INFO, 'WebSocket Connected')

        except Exception as e:
            self.set_ws_status(False)
            set_logger(LogType.LT_WARNING, f'WebSocket Connect Failed: {e}')

    def queue_prompt(self, prompt):
        try:
            p = {"prompt": prompt, "client_id": self.client_id}
            data = json.dumps(p).encode('utf-8')
            req = urllib.request.Request(f"http://{self.server_address}:{self.port}/prompt", data=data)
            return json.loads(urllib.request.urlopen(req).read())
        except Exception as e:
            set_logger(LogType.LT_EXCEPTION, str(e))
            raise e

    def get_history(self, prompt_id):
        try:
            with urllib.request.urlopen(f"http://{self.server_address}:{self.port}/history/{prompt_id}") as response:
                return json.loads(response.read())
        except Exception as e:
            set_logger(LogType.LT_EXCEPTION, str(e))
            raise e

    def thread_execute(self, func, *args, timeout=20):
        que = queue.Queue()

        def wrapper_func():
            try:
                result = func(*args)
            except Exception as e:
                result = e
            que.put(result)

        thread = threading.Thread(target=wrapper_func)
        thread.daemon = True
        thread.start()

        try:
            result = que.get(block=True, timeout=timeout)
        except queue.Empty:
            raise Exception(f"TimeOut Error")
        if isinstance(result, Exception):
            raise result
        return result

    def get_images(self, prompt, timeout):
        try:
            self.ws = websocket.WebSocket()
            self.ws.connect(f"ws://{self.server_address}:{self.port}/ws?clientId={self.client_id}",
                            ping_interval=None)
            prompt_id = self.queue_prompt(prompt)['prompt_id']
            while True:
                self.ws.settimeout(timeout)
                out = self.ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    if message['type'] == 'executing':
                        data = message['data']
                        if data['node'] is None and data['prompt_id'] == prompt_id:
                            break  # Execution is done
                else:
                    continue  # previews are binary data
            history = self.get_history(prompt_id)
            self.ws.close()
            return history[prompt_id]

        except Exception as e:
            raise e

    def que_and_rcv_data(self, prompt, timeout):
        try:
            max_attempts=2
            attempts = 0
            while attempts < max_attempts:
                try:
                    self.get_images(prompt, timeout)
                    break

                except Exception as e:
                    attempts += 1
                    set_logger(LogType.LT_WARNING, f'Timeout Error : {attempts}th trial')
                    time.sleep(1)

            if attempts >= max_attempts:
                raise Exception("Timeout Error")

        except Exception as e:
            set_logger(LogType.LT_EXCEPTION, str(e))
            raise e

    def run(self):
        while not self.get_app_status():
            if not self.get_ws_status():
                self.ws_reconnect()

            if self.get_ws_status():
                try:
                    msg = self.ws.recv()
                    if msg == None:
                        self.set_ws_status(False)
                        raise Exception
                    else:
                        self.set_ws_status(True)
                        msg = json.loads(msg)
                        if msg['type'] == 'executing':
                            self.recv_queue.put(msg)

                except ConnectionRefusedError as e:
                    set_logger(LogType.LT_WARNING, f"WebSocketConnectionClosedException: {str(e)}")
                    self.set_ws_status(False)

                except Exception as e:
                    set_logger(LogType.LT_EXCEPTION, str(e))
                    self.set_ws_status(False)

            else:
                time.sleep(5)  # wait for reconnection

    def close(self):
        try:
            self.set_app_status(True)

            if self.receiveThread != None:
                self.receiveThread.join()
                self.receiveThread = None

            if self.ws != None:
                self.ws.close()
                self.ws = None
            set_logger(LogType.LT_INFO, 'Close WebSocketClientWorker')

        except Exception as e:
            set_logger(LogType.LT_EXCEPTION, str(e))


if __name__ == "__main__":
    from cmd_args import parse_args
    import os

    args = parse_args()
    client = WebSocketClient(args)

    def preparation(client):
        try:
            with open(os.path.join(args.workflow_dir, 'cache_ckpt.json'), 'r', encoding='utf-8') as f:
                prompt = json.load(f)
                client.que_and_rcv_data(prompt, 15)
                time.sleep(1)
            return
        except Exception as e:
            raise e

    idx = 1
    while True:
        if idx == 100:
            break
        preparation(client)
        print(idx)