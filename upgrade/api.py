from flask import jsonify
from flask_restful import Resource
from flask_restful import request

from upgrade.infosite import get_release_cache
from upgrade.task import get_result
from upgrade.task import schedule
from upgrade.task import revoke_task
from rest import RestApi

rest = RestApi(base_route="/upgrade/v1/")


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
        sample post body for image:
        {
            "platform": "fos" # "only support fos for now",
            "build_info": {
                "product": "FAC" (later) // No need for FGT/FWF
                "repo": "FortiOS-6K7K"
                "branch": "", "" for main branch
                "release": "7.0.0"
                "build": int,
                "type": "image",
                "file_pattern": null, // no need for FortiOS and FortiOS-6K7K
                "debug": true/false // when true, use debug image.,
                "verify": true/false // by default this is true,
                "use_cache": true/false // by default it is true,
                "force": true/false // force upgrade even existing job running
            }
            "device_access": {
                "host": "xxxx",
                "username": "xxxx",
                "password": "xxxx"
            }
        }

        For  packages: av / aveng, ips / ipseng malware
        {
            "platform": "fos" # "only support fos for now",
            "build_info": {
                "product": "FGT" (later) // No need for FGT/FWF
                "type": "pkg",
                "pkgs": [               // you can input some of the category
                    "avsig": {          // if you don`t want to upgrade all
                        "release": "7.0.0",
                        "build_list": {
                            "ETDB.High": "90.08471",
                            "FLDB": "90.08471",
                            "MMDB": "90.08471"
                        }
                    },
                    "aveng": {
                        "release": "7.0.0",
                        "build": "xxxx"
                    },
                    "ipssig": {
                        "release": "7.0.0",
                        "build_list": {
                            "isdb": "90.08471",
                            "nids": "90.08471",
                            "apdb": "90.08471"
                        }
                    },
                    "ipseng": {
                        "release": "7.0.0",
                        "build": "xxxx"
                    },
                    "malware": {
                        "release": "7.0.0",
                        "build": "xxxx"
                    }
                ],
                "verify": true/false,
                "file_pattern": null, // no need for FortiOS and FortiOS-6K7K
                "use_cache": true/false, // by default it is true
                "force": true/false // force upgrade even existing job running
            }
            "device_access": {
                "host": "xxxx",
                "username": "xxxx",
                "password": "xxxx"
            }
        }
        :return: {"upgrade_id": "xxxxxx"}
        :rtype: json
        """
        data = request.json
        ret = schedule(data)
        return jsonify(ret)

    def delete(self, upgrade_id):
        """
        stop upgrade task
        :param upgrade_id: upgrade id to stop
        :type upgrade_id: str
        :return: null
        :rtype: null
        """
        revoke_task(upgrade_id)


@rest.route("releases")
class Releases(Resource):
    def get(self):
        releases = get_release_cache()
        return "\n".join(releases)
