from flask import jsonify
from flask_restful import Resource, request

import pool.manager as manager
from rest import RestApi

rest = RestApi(base_route="/mutualpool/v1/")


@rest.route("fortitoken/create")
class CreatePool(Resource):
    def post(self):
        data = request.json
        manager.create_fortitoken_pool(data)
        return jsonify({"result": "created"})


@rest.route("fortitoken/request/<string:fortigate_ip>")
class FetchFortiToken(Resource):
    def get(self, fortigate_ip):
        res = manager.fetch_fortitoken_from_fortitoken_pool(fortigate_ip)
        return jsonify(res)


@rest.route("fortitoken/release")
class ReleaseFortitokenList(Resource):
    def post(self):
        data = request.json
        manager.release_fortitoken_list(data)
        return jsonify(True)


@rest.route("fortitoken/check/<string:fortigate_ip>")
class CheckFortiToken(Resource):
    def get(self, fortigate_ip):
        res = manager.check_pool(fortigate_ip)
        return jsonify(res)
