import base64
from io import BytesIO

import psutil
import pyscreenshot


def get_screen_shot():
    screen_capture = pyscreenshot.grab()
    buffer = BytesIO()
    screen_capture.save(buffer, format='png')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str


def kill_process(proc_name):
    if proc_name is None or len(proc_name) == 0:
        return "Please specify process_name"
    proc_name = proc_name.lower()
    process_list = list(
        filter(
            lambda x: proc_name in x.name().lower(),
            psutil.process_iter()
        )
    )
    list(map(lambda x: x.terminate(), process_list))
    gone, alive = psutil.wait_procs(process_list, timeout=5)
    return f"gone: {len(gone)}, alive: {len(alive)}"


def get_proc_status(proc_name):
    if proc_name is None or len(proc_name) == 0:
        return "Please specify process_name"
    proc_name = proc_name.lower()
    process_list = list(
        filter(
            lambda x: proc_name in x.name().lower(),
            psutil.process_iter()
        )
    )
    status = any(process_list)
    return "live" if status else "exited"
