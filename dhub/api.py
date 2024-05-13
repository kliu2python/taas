# pylint: disable=no-name-in-module
import os

from flask import jsonify
from flask_restful import Resource, request

import utils.android as android_lib
import dhub.manager as device_hub_lib
from args import parser
from dhub.manager import (
    init_device_hub,
    launch_emulator,
    delete_emulator,
    check_emulator,
    list_emulators,
    list_node
)
from rest import RestApi

rest = RestApi(base_route="/dhub")
init_device_hub()


@rest.route("cleandevice")
class CleanEmulatorAndroidUserDataApi(Resource):
    def get(self):
        args = parser.parse_args()
        avd_name = args['avd_name']
        if not avd_name:
            return "Error: Please specify avd name"
        avd_path = os.path.expanduser("~/.android/avd")
        avd_path = os.path.join(avd_path, f"{avd_name}.avd")
        if os.path.exists(avd_path):
            android_lib.clean_emulator_android_user_data(avd_path)
            return 'SUCCESS'
        return f"Error: avd path {avd_path} is not found"


@rest.route("getdevice")
class GetDeviceApi(Resource):
    def get(self):
        args = parser.parse_args()
        platform_id = args['platform_id']
        device_name = device_hub_lib.assign_device(platform_id)
        return device_name if device_name else "Fail"


@rest.route("recycledevice")
class RecycleDeviceApi(Resource):
    def get(self):
        args = parser.parse_args()
        avd_name = args['avd_name']
        request_id = args['request_id']
        platform_id, slot = device_hub_lib.get_device_slot_platform(avd_name)
        return device_hub_lib.recycle_device(
            platform_id, slot, request_id
        )


@rest.route("internal/registernodeip")
class RegisterNodeIp(Resource):
    def get(self):
        host = device_hub_lib.get_host_obj()
        if host.running_mode in ["node"]:
            return "Error: Running in node, not supported"
        args = parser.parse_args()
        ip = args['ip']
        device_hub_lib.get_host_obj().register_ip(ip)
        return "SUCCESS"


@rest.route("manage/showdeviceslots")
class ShowDeviceSlotsApi(Resource):
    def get(self):
        return device_hub_lib.show_device_slot()


@rest.route("manage/showhostips")
class ShowHostAvaliableIps(Resource):
    def get(self):
        return device_hub_lib.get_host_obj().ips


@rest.route("deviceoperation")
class DeviceOperation(Resource):
    def post(self):
        args = parser.parse_args()
        avd_name = args['avd_name']
        request_id = args['request_id']
        op_data = request.json
        return device_hub_lib.option_device(avd_name, request_id, **op_data)


@rest.route("/emulator/create")
class LaunchEmulator(Resource):
    """
    post body:
    {
        "os": "android",
        "version: "14",
        "dns": None
    }
    """
    def post(self):
        data = request.json
        results = launch_emulator(data)
        return jsonify({"results": results})


@rest.route("/emulator/delete")
class DeleteEmulator(Resource):
    """
    post body:
    {
        "pod_name": "xxxxxx"
    }
    """
    def post(self):
        data = request.json
        results = delete_emulator(data)
        return jsonify({"results": results})

@rest.route("/emulator/check")
class CheckEmulator(Resource):
    """
    post body:
    {
        "pod_name": "xxxxxx"
    }
    """
    def post(self):
        data = request.json
        results = check_emulator(data)
        return jsonify({"results": results})


@rest.route("/emulator/list")
class ListAllEmulator(Resource):
    def get(self):
        results = list_emulators()
        return jsonify({"results": results})


@rest.route("/node/list")
class ListAllSeleniumNode(Resource):
    def get(self):
        results = list_node()
        return jsonify({"count": len(results), "results": results})

