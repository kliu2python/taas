from flask import jsonify, request
from flask_restful import Resource

from rest import RestApi
from jenkins_cloud.manager import JenkinsJobs, extract_job_path
from utils.MongoDBAPI import MongoDBAPI

rest = RestApi(base_route="/api/v1/jenkins_cloud")
runner = JenkinsJobs()


def fetch_auth_info_by_job_name(job_name):
    job_info = MongoDBAPI().get_job_by_name(f"name={job_name}")
    return job_info.get("documents")[0]


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


@rest.route("/execute/job")
class ExecuteJobsByName(Resource):
    def post(self):
        data = request.get_json()
        parts = data.get('server_ip').split('/')
        server_ip = f"{parts[0]}//{parts[2]}"
        try:
            results = JenkinsJobs(
                server_ip,
                data.get('server_un'),
                data.get('server_pw')
            ).execute_job(data)
        except Exception:
            return "auth failed", 500
        return results, 200


@rest.route("/jobs")
class ListAllSavedJobs(Resource):
    def get(self):
        results = runner.get_all_saved_jobs()
        return results, 200


@rest.route("/jobs/<string:job_name>")
class DeleteJobByName(Resource):
    def delete(self, job_name):
        results = runner.delete_saved_jobs(job_name)
        return results, 200


@rest.route("/jobs/<string:job_name>")
class GetOneSavedJob(Resource):
    def get(self, job_name):
        results = runner.get_one_saved_job(job_name)
        return results, 200


@rest.route("/jobs/build/result")
class GetJobBuildResultByBuildNumber(Resource):
    def get(self):
        job_name = request.args.get("job_name")
        build_num = request.args.get("build_number")
        job_info = fetch_auth_info_by_job_name(job_name)
        if not job_info:
            return f"no job {job_name} found", 500
        parts = job_info.get('server_ip').split('/')
        server_ip = f"{parts[0]}//{parts[2]}"
        job_path = extract_job_path(job_info.get('server_ip'))
        try:
            results = JenkinsJobs(
                server_ip, job_info.get('server_un'), job_info.get('server_pw')
            ).fetch_build_res_using_build_num(job_path, build_num, job_name)
        except Exception:
            return "auth failed", 500
        return results, 200


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
