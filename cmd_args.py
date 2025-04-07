import argparse
import json
import os

def parse_args():
    base_dir = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser()

    # Redis Settings
    parser.add_argument('--redis_host', default='192.168.1.41')  #192.168.1.41  , 166
    parser.add_argument('--redis_port', default='6379')   # 6379
    # parser.add_argument('--redis_pwd', default='!xorbis21569100')
    parser.add_argument('--redis_conn_delay', default=0.2)

    # AI content Settings
    parser.add_argument('--input_dir', default=os.path.join(base_dir, 'input'))
    parser.add_argument('--output_dir', default=os.path.join(base_dir, 'output'))
    parser.add_argument('--workflow_dir', default=os.path.join(base_dir, 'data', 'workflow'))

    # ComfyUI settings
    parser.add_argument('--comfy_path', default=r'C:\Users\chsjk\PycharmProjects\ComfyUI_windows_portable')
    parser.add_argument('--comfy_host', default='127.0.0.1')
    parser.add_argument('--comfy_port', default='8188')

    args,_ = parser.parse_known_args()
    return args