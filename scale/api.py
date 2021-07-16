import datetime
import json

from flask import jsonify, make_response, render_template_string, send_file
from flask_restful import Resource, request

import scale.controller as controller
from args import parser
from rest import RestApi
from scale.constants import COMMANDLOG_TEMPLATE

rest = RestApi(base_route="/scalecontroller/")


@rest.route("createsession")
class CreateSession(Resource):
    """
    post data example:
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

    def post(self):
        op_data = request.json
        results = controller.create_session(**op_data)
        return jsonify({"results": results})


@rest.route("updatesession")
class UpdateSession(Resource):
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

    def put(self):
        op_data = request.json
        sess_id = op_data.pop("session_id")
        results = controller.update_session(
            **op_data, session_id=sess_id
        )
        return jsonify({"results": results})


@rest.route("updaterunner")
class UpdateRunner(Resource):
    """
    request body:
    {
        "session_id": str,
        "runners": list [start, end] ,
                   or int, if use int, momentum will not be used
        "momentum": int
    }
    """

    def patch(self):
        op_data = request.json
        sess_id = op_data.pop("session_id")
        results = controller.update_runner(
            op_data, session_id=sess_id
        )
        return jsonify({"results": results})


@rest.route("stopsession/<string:session_id>")
class StopSession(Resource):
    """
    post data type:
    {
        session_id: id
    }
    """

    def delete(self, session_id):
        results = controller.quit_session(session_id)
        return jsonify({"results": results})


@rest.route("showsession/<string:session_id>")
class ShowSession(Resource):
    def get(self, session_id):
        def default(x):
            if isinstance(x, datetime.datetime):
                return f"{x}"
            return type(x).__qualname__

        results = controller.read_session(session_id)
        json_dumps = json.dumps(
            results,
            default=default
        )
        return json.loads(json_dumps)


@rest.route(
    "showsession/<string:session_id>/<string:device_type>/"
    "<string:category>/<int:count>"
)
class ShowSessionCommandLog(Resource):
    def get(self, session_id, device_type, category, count=0):
        """
        Get crash log in text
        session_id: session id for the crashlog
        count: how many crash logs want to display
        0 : all
        n: last n number
        """
        session_query = f"{session_id}_{device_type}_{category}"
        results = controller.read_session(
            session_query,
            keys={"common": ["command_log"]}
        ).get("command_log", [])
        ret = ""
        if results:
            args = parser.parse_args()
            ops = args.get("ops")
            download_request = ops in ["download"]
            if count == 0 or download_request:
                logs = results
            elif count > 0:
                logs = results[-count:]
            else:
                return "Error: count must be >= 0"
            if logs:
                if download_request:
                    tmp_file = f"{session_query}.log"
                    with open(tmp_file, "w") as FILE:
                        FILE.writelines(logs[len(logs):0:-1])
                    response = send_file(
                        filename_or_fp=tmp_file,
                        mimetype="application/octet-stream",
                        as_attachment=True,
                        attachment_filename=tmp_file,
                        cache_timeout=0
                    )
                    return response
                else:
                    for i in range(1, len(logs) + 1):
                        item = logs[-i].replace("\n", "<br>")
                        ret += f"<br>{item}<br><br>"
            html = COMMANDLOG_TEMPLATE.format(category=category,
                                              command_logs=ret)
            headers = {'Content-Type': 'text/html'}
            return make_response(render_template_string(html), 200, headers)


@rest.route("listsession/<string:session_type>")
class ListSession(Resource):
    def get(self, session_type):
        results = controller.list_session(session_type)
        return jsonify(results)


@rest.route("listworker")
class ListWorker(Resource):
    def get(self):
        results = controller.list_worker()
        return jsonify(results)
