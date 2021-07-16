# pylint: disable=no-self-use,too-few-public-methods,no-name-in-module
# pylint: disable=duplicate-code
from flask_restful import Resource

from rest import RestApi, get_loaded_api

rest = RestApi(base_route="")


@rest.route("/")
class Welcome(Resource):
    def get(self):
        return f"Server is Up Running for {get_loaded_api()}"
