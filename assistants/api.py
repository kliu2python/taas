# pylint: disable=no-self-use,too-few-public-methods,no-name-in-module

from flask import jsonify
from flask_restful import Resource, request
from pynput.keyboard import Key, Controller

import utils.network as network_lib
import utils.system as system_lib
from args import parser
from rest import RestApi
from utils.logger import get_logger

logger = get_logger()


rest = RestApi(base_route="/")


@rest.route("screencap")
class GetScreenShotApi(Resource):
    def get(self):
        return system_lib.get_screen_shot()


@rest.route("killprocess")
class KillProcessApi(Resource):
    def get(self):
        args = parser.parse_args()
        proc_name = args['process_name']
        return system_lib.kill_process(proc_name)


@rest.route("processstatus")
class GetProcessStatusApi(Resource):
    def get(self):
        args = parser.parse_args()
        proc_name = args['process_name']
        return system_lib.get_proc_status(proc_name)


@rest.route("ping")
class PingCheckApi(Resource):
    def get(self):
        args = parser.parse_args()
        ip = args['ip']
        return network_lib.ping_check(ip)


@rest.route("keyboardinput")
class KeyStroke(Resource):
    def post(self):
        """
        Perform key strokes body format:
        {
            "keys": [
                ["123456", "type"],
                ["enter", "press"]
            ]
        }

        key format: [key_string, key_type]:

        key_type:
           type: text/strings you want to type to screen.
                 use key_string to specify
           press: key names you want to press. use key_string to specify.

        key_string: text to input or button name you want to press

        """

        keyboard = Controller()
        keys = request.json.get("keys", [])
        ret = {"success": [], "fail": []}
        for item in keys:
            try:
                key_str, key_type = item
                if key_type.lower() in ["type"]:
                    keyboard.type(key_str)
                if key_type.lower() in ["press"]:
                    keyboard.press(Key[key_str.lower()])
                ret["success"].append([item])
            except Exception as e:
                logger.exception(f"Error when press key {item}", exc_info=e)
                ret["fail"].append([item])
        return jsonify(ret)
