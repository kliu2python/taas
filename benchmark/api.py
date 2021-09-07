from flask import jsonify
from flask_restful import Resource, request

import benchmark.services.reporting as service
from rest import RestApi

rest = RestApi(base_route="/benchmark/v1/")


@rest.route("result/<string:job_name>/<string:build_id>")
class Result(Resource):
    def get(self, job_name, build_id):
        msg = service.ResultApi.read_all(
            job_name=job_name, build_id=build_id
        )
        return msg

    def post(self):
        """
        post data example:
        {
            "job_name": "BLSM-FGT7040E",         # Jenkins job name
            "build_id": "1234",                  # Jenkins build number
            "platform": "FGT-7040E",             # DUT Model / Platform
            "version": "V6.4.2GA",               # FOS Version on DUT
            "user": "znie",                      # Trigger / Test Owner
            "test": "HTTPCPS_Bidir_V1_0",        # Test Case Name
            "settings": "xxxx",                  # Settings / Comments
            "start_time": "xxxx",                # Run start time
            "end_time": "xxx"                    # Case End Time
        }

        **Schema validation skipped**

        """
        data = request.json
        msg, code = service.ResultApi.create(data)
        return msg, code

    def put(self, job_name, build_id):
        """
        post data example:
        {
            "platform": "FGT-7040E",             # DUT Model / Platform
            "version": "V6.4.2GA",               # FOS Version on DUT
            "user": "znie",                      # Trigger / Test Owner
            "test": "HTTPCPS_Bidir_V1_0",        # Test Case Name
            "policy_setting": "xxxx",            # Policy Setting / Comments
            "start_time": "xxxx",                # Run start time
            "end_time": "xxx",                   # Case End Time
        }

        **Schema validation skipped**

        Put can be any number of all supported fields.
        """
        data = request.json
        msg, code = service.ResultApi.update_one(
            data, job_name=job_name, build_id=build_id
        )
        return msg, code

    def delete(self, job_name, build_id):
        msg, code = service.ResultApi.delete(
            job_name=job_name, build_id=build_id
        )
        return msg, code


@rest.route("/log/counter/<string:job_name>/<string:build_id>/<string:counter>")
class Counter(Resource):
    def get(self, job_name, build_id, counter):
        msg = service.CounterApi.read_all(
            job_name=job_name, build_id=build_id, counter=counter
        )
        return jsonify(msg)

    def post(self):
        """
        {"data":
            [
                {
                    "job_name": "BLSM-FGT7040E",         # Jenkins job name
                    "build_id": "1234",                  # Jenkins build number
                    "idx": "FGT113",                     # device/platform/indx
                    "counter": "cpu",  "memory", "bw"    # Perf counter
                    "datetime": "xxxx"                  # FOS Version on DUT
                    "value": "TEXT VALUE",               # Trigger / Test Owner
                }
            ]
        }

        **Schema validation skipped**

        "value" field is TEXT, please covert if you need other types.

        """
        data = request.json
        status_code = 201
        resp_msg = None
        for d in data["data"]:
            msg, code = service.CounterApi.create(d)
            if code > status_code:
                status_code = code
                resp_msg = msg
        return resp_msg, status_code

    def delete(self, job_name, build_id):
        msg, code = service.CounterApi.delete(
            job_name=job_name, build_id=build_id
        )
        return msg, code


@rest.route("log/crash/<string:job_name>/<string:build_id>/<string:case_name>")
class CrashLog(Resource):
    def get(self, job_name, build_id, case_name):
        msg = service.CrashLogApi.read_all(
            job_name=job_name, build_id=build_id, case_name=case_name
        )
        return jsonify(msg)

    def post(self):
        """
        post data example:
        {
            "job_name": "BLSM-FGT7040E",         # Jenkins job name
            "build_id": "1234",                  # Jenkins build number
            "platform": "FGT-7040E",             # DUT Model / Platform
            "version": "V6.4.2GA",               # FOS Version on DUT
            "timestamp": "xxx", (Optional)       # Trigger / Test Owner
            "test": "test name" (not required)   # Test Case Name
            "log": "xxxx",                       # Crash log content
        }

        **Schema validation skipped**

        """
        data = request.json
        msg, code = service.CrashLogApi.create(data)
        return msg, code

    def delete(self, job_name, build_id):
        msg, code = service.CrashLogApi.delete(
            job_name=job_name, build_id=build_id
        )
        return msg, code


@rest.route("log/command/<string:job_name>/<string:build_id>")
class CommandLog(Resource):
    def get(self, job_name, build_id):
        msg = service.CommandLogApi.read_all(
            job_name=job_name, build_id=build_id
        )
        return jsonify(msg)

    def post(self):
        """
        post data example:
        {
            "job_name": "BLSM-FGT7040E",         # Jenkins job name
            "build_id": "1234",                  # Jenkins build number
            "timestamp": "xxx", (Optional)       # Trigger / Test Owner
            "command": "test name"               # commands
            "log": "xxxx",                       # command log content
        }

        **Schema validation skipped**

        """
        data = request.json
        msg, code = service.CommandLogApi.create(data)
        return msg, code

    def delete(self, job_name, build_id):
        msg, code = service.CommandLogApi.delete(
            job_name=job_name, build_id=build_id
        )
        return msg, code
