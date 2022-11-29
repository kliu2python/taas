from flask import jsonify
from flask_restful import Resource
from flask_restful import request

from upgrade.statics import count_access
from upgrade.task import get_result
from upgrade.task import update
from upgrade.task import revoke_task
from rest import after_request
from rest import RestApi

rest = RestApi(base_route="/upgrade/v1/")


@after_request(count_access)
@rest.route("update/<string:upgrade_id>")
class Update(Resource):
    def get(self, upgrade_id):
        """
        get task status
        :param upgrade_id: task id when created
        :type upgrade_id: str
        :return: "inprogress" or "completed"
        :rtype: str
        """
        return get_result(upgrade_id)

    def post(self):
        """
        sample post body:
        {
            "platform": "fos" # "only support fos for now",
            "build_info": {
                "version": "v7.00",
                "product": "FAC" (later) // No need for FGT/FWF
                "repo": "FortiOS-6K7K"
                "branch": "", "" for main branch
                "release": "7.0.0"
                "build": int,
                "type": "image",
                "file_pattern": null, // no need for FortiOS and FortiOS-6K7K
                "debug": true/false // when true, use debug image.
            }
            "device_access": {
                "ip": "xxxx",
                "username": "xxxx",
                "password": "xxxx"
            }
        }
        :return: {"upgrade_id": "xxxxxx"}
        :rtype: json
        """
        data = request.json
        upgrade_id = update(data)
        return jsonify({"upgrade_id": upgrade_id})

    def delete(self, upgrade_id):
        revoke_task(upgrade_id)
