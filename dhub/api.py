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
    delete_emulator_worker,
    check_emulator,
    list_emulators,
    launch_selenium_node,
    delete_selenium_node,
    check_selenium_node,
    check_selenium_host_point,
    check_android_status,
    send_adb_command
)
from rest import RestApi

rest = RestApi(base_route="/dhub")
init_device_hub()


@rest.route("/ready")
class Readiness(Resource):
    def get(self):
        return "Ready"


@rest.route("/healthz")
class Liveness(Resource):
    def get(self):
        return "Healthy"


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
        return jsonify({"pod_name": results})


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
        results = delete_emulator_worker(data)
        return jsonify({"results": results})


@rest.route("/emulator/check/<string:pod_name>")
class CheckEmulator(Resource):
    def get(self, pod_name):
        results = check_emulator(pod_name)
        return jsonify({"results": results})


@rest.route("/emulator/device/check/<string:pod_name>")
class CheckAndroidStatus(Resource):
    def get(self, pod_name):
        results = check_android_status(pod_name)
        return jsonify({"results": results})


@rest.route("/emulator/adb/<string:pod_name>/<string:input_text>")
class EnterADBCommandLine(Resource):
    def post(self, pod_name, input_text):
        results = send_adb_command(pod_name, input_text)
        return jsonify({"results": results})


@rest.route("/emulator/list/<string:user>")
class ListAllEmulator(Resource):
    def get(self, user):
        results = list_emulators(user)
        return jsonify({"results": results})


@rest.route("/selenium/create")
class LaunchSeleniumNode(Resource):
    """
    post body:
    {
        "browser": "chrome",
        "version: "125.0",
        "node_name": "chrome-1234",
        "portal_ip": [{'10.160.83.140', 'ftc.fortinet.com'}]
    }
    """
    def post(self):
        data = request.json
        results = launch_selenium_node(data)
        return jsonify({"pod_name": results})


@rest.route("/selenium/delete/<string:pod_name>")
class DeleteSeleniumNode(Resource):
    def post(self, pod_name):
        results = delete_selenium_node(pod_name)
        return jsonify({"results": results})


@rest.route("/selenium/check/<string:pod_name>")
class CheckSeleniumNodeStatus(Resource):
    def get(self, pod_name):
        results = check_selenium_node(pod_name)
        return jsonify({"results": results})


@rest.route("/selenium/check/<string:pod_name>")
class CheckHostPoint(Resource):
    def post(self, pod_name):
        data = request.json
        results = check_selenium_host_point(pod_name, data)
        return jsonify({"results": results})
