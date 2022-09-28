from flask_restful import Resource, Api
from flask import Flask, jsonify, request, make_response

from bp.common import process as pros
from rest import RestApi

rest = RestApi(base_route="/bp/")


@rest.route("run")
class BpRun(Resource):
    def post(self):
        data = request.get_json()
        bp_runid = pros.call_bp(data)
        return make_response(jsonify({"run_id": bp_runid}), 201)


@rest.route("report/<int:runid>")
class BpReport(Resource):
    def get(self, runid):
        data = request.get_json()

        ret = pros.report_analysis(data, runid)
        ret = ret.to_json(orient="records")
        return make_response(jsonify({"run_id": ret}), 200)

    # stop bp run
    def delete(self, runid):
        data = request.get_json()
        key_stop = pros.stop_run(data, runid)
        return make_response(jsonify({"stop_status": str(key_stop)}), 202)
