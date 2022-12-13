from flask import jsonify
from flask_restful import Resource, request

import resources.manager as manager
from rest import RestApi

rest = RestApi(base_route="/resourcesmanager/v1/")


@rest.route("pool/create")
class CreatePool(Resource):
    """
    Create a resource pool, note: custom resource should be same as standard
    resource structure.
    http://localhost:8000/resourcesmanager/v1/pool/create

    Note: "ftc_cert", "ftc_key" are shared across all Dev Env, so we might
    not need in the post body yet. this will be in config

    post body:
    {
        "id": "v6.4.2-pool",
        "type": "fortigate.user" / "fac.user"
        "group": "resource group" (optional, used when you have pool aggration)
        "life": 60,
        "res_life": 3,
        "prepare": true,
        "capacity": 20,
        "data": {
            "ip": "10.160.50.132",
            "admin_user": "admin",
            "admin_password": "fortinet",
            "fgt_token": "xxxxxxx",
            "user_password": "fortinet",
            "email": "znie@fortinet.com",
            "user_prefix": "test_fgt",
            "group": "ssl_vpn_group",
            "phone": "+16509655818",
            "mfa_provider": None or "fortitoken" or "fortitoken-cloud"
            "ftc": {
                "ftc_server": "10.160.11.130:8686",
                "db_ip": "10.160.11.39",
                "db_user": "fas",
                "db_pw": "fas",
                "db_name": "fas",
                "mfa_type": "ftm",
                "mfa_device": "android"
            },
            "custom_data": {
                "fgt_ip": "10.160.50.132",
                "sslvpn_port": 10443
            }
        },
        "resource": []
    }
    """
    def post(self):
        data = request.json
        results = manager.create_pool(data)
        return jsonify({"results": results})


@rest.route("pool/list")
class ListPool(Resource):
    """
    Show avaliable resrouce pools
    http://localhost:8000/resourcesmanager/v1/pool/list
    """
    def get(self):
        results = manager.list_pool()
        return jsonify({"results": results})


@rest.route("pool/statics/<string:pool_id>")
class PoolStatics(Resource):
    """
    localhost:8000/resourcesmanager/v1/pool/statics/<pool_id>
    """
    def get(self, pool_id):
        results = manager.get_pool_statics(pool_id)
        return jsonify(results)


@rest.route("pool/show/<string:pool_id>")
class ShowPool(Resource):
    """
    localhost:8000/resourcesmanager/v1/pool/show/<pool_id>
    """
    def get(self, pool_id):
        results = manager.show_pool(pool_id)
        return jsonify(results)


@rest.route("pool/delete/<string:pool_id>")
class DeletePool(Resource):
    """
    Show avaliable resrouce pools
    localhost:8000/resourcesmanager/v1/pool/delete/<pool_id>
    """
    def delete(self, pool_id):
        results, status_code = manager.delete_pool(pool_id)
        return results, status_code


@rest.route("res/request/<string:pool_id>")
class GetResource(Resource):
    """
    localhost:8000/resourcesmanager/v1/res/request/<pool_id>
    """
    def get(self, pool_id):
        results, status_code = manager.request_resource(pool_id)
        return results, status_code


@rest.route("res/otp/generate/<string:pool_id>/<string:resource_id>")
class GenerateTotpCode(Resource):
    """
    localhost:8000/resourcesmanager/v1/res/opt/generate/<pool_id>/<resource_id>
    """
    def get(self, pool_id, resource_id):
        results, status_code = manager.generate_otp(pool_id, resource_id)
        return {"otp": results}, status_code


@rest.route("res/renew")
class RenewResource(Resource):
    def put(self):
        return "NOT SUPPORTED"


@rest.route("res/recycle/<string:pool_id>/<string:res_id>")
class RecycleResource(Resource):
    """
    http://localhost:8000/resourcesmanager/v1
    /res/recycle/<pool_id>>/<resource_id>
    e.g.
    http://localhost:8000/resourcesmanager/v1
    /res/recycle/10.160.16.50-pool/f632020b-9f8a-48d6-91fc-f4399760ba9d
    """
    def delete(self, pool_id, res_id):
        results, status_code = manager.recycle_resource(pool_id, res_id)
        return results, status_code


@rest.route("fgt/setup")
class SetupConfiguration(Resource):
    """
    Automatic setup configuration of new deployed FGT
    http://localhost:8000/resourcesmanager/v1/fgt/setup
    e.g.
    post body:
    {
        "fgt_ip": "10.160.50.140",
        "radius_ip": "10.160.13.32",
        "hostname": "automation_6_6_0_140"
    }
    """
    def post(self):
        try:
            data = request.get_json(force=True)
            result = manager.fgt_setup(
                data["fgt_ip"], data["radius_ip"], data["hostname"]
            )
        except Exception as err:
            return f"Error: {err}"
        return jsonify(f"result: {result}")
