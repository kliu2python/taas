from flask_restful import Resource

import datasync.constants as constants
from datasync.caches import TaskCache
from rest import RestApi

rest = RestApi(base_route="/datasync/v1/")
cache = TaskCache()


@rest.route("task")
class DataSync(Resource):
    def get(self):
        """
        get task status
        """
        status = cache.get("running")

        if status == 1:
            return "RUNNING"
        return "STOPPED"

    def post(self):
        """
        start task
        """
        cache.set("running", 1)
        return "OK", 201

    def delete(self):
        """
        stop running
        """
        for key in constants.CACHE_KEY.keys():
            cache.set(key, 0)
