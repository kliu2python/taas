from flask import jsonify
from flask_restful import Resource

from rest import RestApi
from jenkins_job.manager import JenkinsJobs

rest = RestApi(base_route="/api/v1/jenkins")
runner = JenkinsJobs()


@rest.route("/list")
class ListAllJobs(Resource):
    def get(self):
        results = runner.list_all_jobs_recursive()
        return jsonify({"results": results})


@rest.route("/category/<string:_type>")
class ListAllCategoryByType(Resource):
    def get(self, _type):
        results = runner.get_all_category(_type)
        return jsonify({"results": results})


@rest.route("/jobs/<string:category>")
class ListAllJobsByCategory(Resource):
    def get(self, category):
        results = runner.get_all_jobs(category)
        return jsonify({"results": results})





