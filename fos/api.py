from flask import jsonify
from flask_restful import Resource

from fos.conf import CONF
from rest import RestApi
from utils.mongodb import MongoDB

rest = RestApi(base_route="/fos/v1/")
db = MongoDB(CONF.get("db"), "fos")


@rest.route(
    "features/<string:version>/<string:branch>/<string:platform>/<string:build>"
)
class Features(Resource):
    def get(self, version, branch, platform, build="latest"):
        if branch in ["trunk"]:
            branch = ""

        query = {
            "major_version": version,
            "branch": branch
        }

        if build in ["latest"]:
            latest_build = db.find_one(query, "versions")
            build = latest_build["build"]

        query["build"] = build
        query["name"] = platform

        res = db.find_one(query, "models")

        return jsonify(res)
