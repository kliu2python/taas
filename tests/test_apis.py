import base64
import json
from io import BytesIO

from PIL import Image

from services.utils.rest import rest_call
from services.utils.threads import thread_run, ThreadsManager


def get_base64_string_image(file_path):
    img = Image.open(file_path)
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    return base64.b64encode(img_bytes.getvalue()).decode()


def res_call(param):
    ret = rest_call(
        "10.160.13.11", "/imageclassifier", method="post",
        json=json.dumps(param)
    )
    print(ret.decode())


def test_image_classifier_api():
    param = {"inputs": [get_base64_string_image(
        r"C:\Users\znie\Documents\mydocker\DL_services\collected_data"
        r"\forticlassifier\google_mail_home"
        r"\4.png")]
    }
    calls = []
    total_calls = 0
    for _ in range(2000):
        for _ in range(6):
            calls.append(thread_run(res_call, param=param))
        ThreadsManager().wait_for_complete(caller_ids=calls)
        total_calls += len(calls)
        calls = []
        print(f"total calls: {total_calls}")
