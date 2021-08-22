from flask import jsonify, make_response, render_template_string, send_file
from flask_restful import Resource, request

import scale.session.controller as controller
import scale.services.user as user_api
import scale.services.log as log_api
from args import parser
from rest import RestApi
from scale.common.constants import COMMANDLOG_TEMPLATE

rest = RestApi(base_route="/scale/v1/")


@rest.route("plan/<string:user>/<string:name>")
class Plan(Resource):
    def get(self, user=None, name=None):
        if user is None:
            msg = user_api.Plan.read_to_json()
        else:
            param = {}
            if user:
                param["user"] = user
            if name:
                param["name"] = name
            msg = user_api.Plan.read_to_json(**param)
        return msg

    def post(self):
        """
        post data example:
        {
            "user_name": "znie",
            "name": "ftc_perf",
            "target_platform": "ftc",
            "runner_count": [1, 50],
            "loop": "true",
            "wait_seconds_after_notify": 20,
            "deployment_config": "runner_deployment_ftc.yaml",
            "pods_adjust_momentum": 1,
            "force_new_session": false,
            "devices": ["device2", "device2"],
            "duration": 24
        }
        """
        data = request.json
        msg, code = user_api.Plan.create(data, pk=["user", "name"])
        return msg, code

    def put(self, user=None, name=None):
        data = request.json
        msg, code = user_api.Plan.update_one(data, user=user, name=name)
        return msg, code

    def delete(self, user, name):
        msg, code = user_api.Plan.delete(user=user, name=name)
        return msg, code


@rest.route("device/<string:user>/<string:name>")
class Device(Resource):
    def get(self, user=None, name=None):
        """
        scale/v1/device : get all devices for all users
        scale/v1/device/<user name>: get all devices for user: <user name>
        scale/v1/device/<user name>/<name>: get a device named <name>
                                     under user: <user name>
        """
        if user is None:
            msg = user_api.Device.read_to_json()
        else:
            param = {}
            if user:
                param["user"] = user
            if name:
                param["name"] = name
            msg = user_api.Device.read_to_json(**param)
        return jsonify(msg)

    def post(self):
        """
        {
            "user": "znie",
            "name": "FGT-6501F-2",
            "version": "RC1",
            "status": 1,
            "protocol": "ssh",
            "type": "fgt",
            "credential": {
                "username": "fortinet",
                "password": "fortinet"
            },
            "ip": "10.160.16.50",
            "logging": [
                {
                    "type": "fgt",
                    "category": "general",
                    "commands": [
                        "config global",
                        "diag sys top-mem 200 | grep fas"
                    ]
                },
                {
                    "type": "fgt",
                    "category": "crashlog"
                }

            ]
        }
        """
        data = request.json
        msg, code = user_api.Device.create(data, pk=["user", "name"])
        return msg, code

    def put(self, user, name):
        """
        url: scale/v1/device/<user>/<name>
        Note: <user> <name> all required
        {
            "version": "RC2",
            "device_ip": "1.1.1.3"
        }
        """
        data = request.json
        msg, code = user_api.Device.update_one(data, user=user, name=name)
        return msg, code

    def delete(self, user, name):
        """
        url: scale/v1/device/<user>/<name>
        Note: <user> <name> all required
        """
        msg, code = user_api.Device.delete(user=user, name=name)
        return msg, code


@rest.route("user/<string:name>")
class User(Resource):
    def get(self, name=None):
        """
        url: scale/v1/user : get all users
             scale/v1/user/<name>: get user info for <name>
        """
        if name is None:
            msg = user_api.User.read_to_json()
        else:
            msg = user_api.User.read_to_json(name=name)
        return jsonify(msg)

    def post(self):
        """
        url: scale/user
        {
            "name": "znie",
            "status": 1, # optinal
            "email": "znie@fortinet.com"
        }
        """
        data = request.json
        msg, code = user_api.User.create(data)
        return msg, code

    def put(self, name):
        """
        url: scale/user/<name>
        {
            "email": "znie1111@fortinet.com",
            "status": "0"
        }
        """
        data = request.json
        msg, code = user_api.User.update_one(data, name=name)
        return msg, code

    def delete(self, name):
        msg, code = user_api.User.delete(name=name)
        return msg, code


@rest.route("session/<string:user>/<string:session_name>")
class Session(Resource):
    def get(self, user, session_name):
        ret_msg, ret_code = user_api.Session.get(
            user=user,
            session_name=session_name
        )
        return ret_msg, ret_code

    def post(self):
        """
        post data example:
        {
            "user": "znie",
            "plan_name": "ftc_perf"
        }

        session creation will need following format:
        {
            "session_id": "ftc-sslvpn",
            "servers": [
                {
                    "ssh_ip": "10.160.41.4",
                    "ssh_user": "labuser",
                    "ssh_password": "fortinet",
                    "target_server_ip": "10.160.11.130"
                },
                {
                    "ssh_ip": "10.160.41.4",
                    "ssh_user": "labuser",
                    "ssh_password": "fortinet",
                    "target_server_ip": "10.160.11.147"
                }
            ],
            "target_platform": "ftc",
            "elastic_search": {
                "query_type": "solo",
                "ftc_server": "10.160.11.130",
                "client_ip": "10.160.50.132",
                "interval": 5
            },
            "runner_count": [1, 50],
            "loop": true,
            "wait_seconds_after_notify": 20,
            "deployment_config": "runner_deployment_ftc.yaml",
            "pods_adjust_momentum": 1,
            "force_new_session": false
        }
        """
        data = request.json
        msg, code = user_api.Session.start(**data)
        return msg, code

    def put(self):
        """
        post data type:
        {
            common_dict: {
                case_list: []
                "fail_log": []
            }
            data_dict: {
                target: hostname_str #required
                status: "waiting", or "running", "created"
                current_case: "xxx",
                case_history: {
                    "PASS": [["Case1", "PASS"]],
                    "FAIL": [["Case2", "FAIL"]]
                }
            }
        }
        """
        data = request.json
        ret_msg, ret_code = user_api.Session.update(data)
        return ret_msg, ret_code

    def patch(self):
        """
        request body:
        {
            "session_id": str,
            "runners": list [start, end] ,
                       or int, if use int, momentum will not be used
            "momentum": int
        }
        """
        data = request.json
        ret_msg, ret_code = user_api.Session.patch(data)
        return ret_msg, ret_code

    def delete(self, user, session_name):
        ret_msg, ret_code = user_api.Session.stop(user, session_name)
        return ret_msg, ret_code


@rest.route(
    "logs/html/<string:session_id>/<string:device_type>/"
    "<string:category>/<int:count>"
)
class LogsHtml(Resource):
    def get(self, session_id, device_type, category, count=0):
        """
        Get crash log in text
        session_id: session id for the crashlog
        count: how many crash logs want to display
        0 : all
        n: last n number
        """
        session_query = f"{session_id}_{device_type}_{category}"
        if count == 0:
            count = 1000
        logs = log_api.CommandLog.get_logs(
            session_name=session_id, log_type=category, limit=count
        )
        ret = ""
        if logs:
            args = parser.parse_args()
            ops = args.get("ops")
            download_request = ops in ["download"]
            if logs:
                if download_request:
                    tmp_file = f"{session_query}.log"
                    with open(tmp_file, "w") as FILE:
                        FILE.writelines(logs)
                    response = send_file(
                        filename_or_fp=tmp_file,
                        mimetype="application/octet-stream",
                        as_attachment=True,
                        attachment_filename=tmp_file,
                        cache_timeout=0
                    )
                    return response

                for i in range(1, len(logs) + 1):
                    item = logs[-i].replace("\n", "<br>")
                    ret += f"<br>{item}<br><br>"
            html = COMMANDLOG_TEMPLATE.format(category=category,
                                              command_logs=ret)
            headers = {'Content-Type': 'text/html'}
            return make_response(render_template_string(html), 200, headers)


@rest.route("sessions/<string:session_type>")
class Sessions(Resource):
    def get(self, session_type):
        results = controller.list_session(session_type)
        return jsonify(results)


@rest.route("worker")
class Worker(Resource):
    def get(self):
        results = controller.list_worker()
        return jsonify(results)
