from flask import jsonify
from flask_restful import Resource
from flask_restful import request

from fos.conf import CONF
from rest import RestApi
from utils.mongodb import MongoDB


rest = RestApi(base_route="/fos/v1/")
db = MongoDB(CONF.get("db"), "fos")


@rest.route("features")
class Features(Resource):
    def get(self):
        query = request.json
        res = db.find(query, "models")
        return jsonify({"d": res})
