from flask import jsonify, request
from flask_restful import Resource

from rest import RestApi
from jenkins_job.manager import JenkinsJobs
from utils.MongoDBAPI import MongoDBAPI

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

@rest.route("/jobs/parameters")
class ListParametersOfJob(Resource):
    def get(self):
        job_path = request.args.get("path")
        results = runner.get_job_parameters(job_path)
        return jsonify({"results": results})


@rest.route("/jobs")
class ListAllSavedJobs(Resource):
    def get(self):
        results = runner.get_all_saved_jobs()
        return jsonify({"results": results})

@rest.route("/jobs/parameters")
class AuthAndParameterCheck(Resource):
    def post(self):
        data = request.json
        parts = data.get('server_ip').split('/')
        server_ip = f"{parts[0]}//{parts[2]}"
        try:
            results = JenkinsJobs(server_ip,
                                  data.get('server_un'),
                                  data.get('server_pw')
                                  ).fetch_job_structure(data)
        except Exception:
            return "auth failed", 500

        return jsonify({"results": results})


@rest.route("/db_jobs")
class ListAllJobsFromDB(Resource):
    def get(self):
        """
        Returns a list of all jobs from the MongoDB database using MongoDBAPI.
        """
        try:
            # Fetch the jobs from the MongoDB using the MongoDBAPI client
            jobs = MongoDBAPI().get_all_jobs()
            return jsonify({"results": jobs})
        except Exception as e:
            return jsonify({"error": "Error fetching job structure on DB"}), 500
