import os
import random
import json
import base64
import cv2
from io import BytesIO
from PIL import Image, ImageOps

from PythonDelegate.src.pythondelegate.funcs import Func1Arg as Delegate
from logger_setup import set_logger, LogType

class AIContent():
    def __init__(self, args):
        try:
            self.args = args
            self.que_and_rcv_data_callback = None
            self.store_redis_data_callback = None
            set_logger(LogType.LT_INFO, 'Init AIContentWorker')

        except Exception as e:
            # set_logger(LogType.LT_EXCEPTION, str(e))
            raise Exception(str(e))

    def set_callbacks(self, que_and_rcv_data_cb, store_redis_data_cb):
        self.que_and_rcv_data_callback = Delegate[object, object]([que_and_rcv_data_cb])
        self.store_redis_data_callback = Delegate[object, object]([store_redis_data_cb])

    def get_prompt(self, workflow_path, input_path, output_path):
        try:
            with open(os.path.join(workflow_path, 'workflow_api.json'), 'r', encoding='utf-8') as f:
                prompt = json.load(f)

            # put input path
            prompt['122']['inputs']['image'] = input_path

            prompt['62']['inputs']['seed'] = random.randint(1,4294967294)
            # save file
            prompt['123']['inputs']['path'] = output_path

            return prompt

        except Exception as e:
            raise e

    def save_byte_image(self, encoded_image, uid):
        image_data = base64.b64decode(encoded_image)
        img = Image.open(BytesIO(image_data))

        img = ImageOps.exif_transpose(img)
        if "A" in img.getbands():
            pass
        else:
            alpha_channel = Image.new("L", img.size, 255)
            img = img.convert("RGBA")
            img.putalpha(alpha_channel)

        input_path = os.path.join(self.args.input_dir, f'{uid}.png')

        img.save(input_path, "PNG")
        return input_path


    def convert_img_to_byte(self, image):
        imageData = cv2.imencode('.png', image)[1].tobytes()
        encoded_image = str(base64.b64encode(imageData), "utf-8")

        return encoded_image

    def get_workflow(self, style):
        workflow_struct = {
            "1" : "van_gogh.json",
            "2" : "pencil_drawing.json"
        }

        return os.path.join(self.args.workflow_dir, workflow_struct[style])

    def preprocess(self, json_message):
        workflow_path = self.get_workflow(json_message['data']['style'])
        # input_path = self.save_byte_image(json_message['data']['image'], json_message['id'])
        input_path = json_message['data']['image']  #for debugging
        output_path = os.path.join(self.args.output_dir, json_message['id'])
        return workflow_path, input_path, output_path

    def run(self, json_message, timeout=5):
        try:
            workflow_path, input_path, output_path = self.preprocess(json_message)
            prompt = self.get_prompt(workflow_path, input_path, output_path)
            self.que_and_rcv_data_callback((prompt, timeout))
            encoded_image = self.convert_img_to_byte(output_path)
            set_logger(LogType.LT_WARNING, f'[Generation]  Success : {json_message["data"]["id"]}')
            response = {
                "id" : json_message['id'],
                "data":
                {
                    "x" : json_message['data']['x'],
                    "y" : json_message['data']['y'],
                    "style" : json_message['data']['style'],
                    "image" : encoded_image
                }
            }
            self.store_redis_data_callback(response)
            return encoded_image

        except Exception as e:
            set_logger(LogType.LT_WARNING, f'[Generation]  Fail :{json_message["data"]["id"]} : {str(e)}')
            raise Exception(e)


    def close(self):
        set_logger(LogType.LT_INFO, 'Close AIContentWorker')


if __name__ == "__main__":
    import cmd_args, torch
    args = cmd_args.parse_args()
    content = AIContent(args)
    content.convert_img_to_byte(torch.load(r'C:\Users\chsjk\Xorbis\2025\1.Projects\2.AI_Graffiti\1.data\3.test_data\vangogh.pth'))