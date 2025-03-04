import os
from logger_setup import LogType, set_logger

def preparation(args):
    try:
        # make directories for program
        dir_list = [
            args.input_dir,
            args.output_dir
        ]
        for d in dir_list:
            if not os.path.exists(d):
                os.makedirs(d, exist_ok=True)
                set_logger(LogType.LT_WARNING, f"Directory '{d}' not found. Created new one.")


    except Exception as e:
        raise Exception(e)

