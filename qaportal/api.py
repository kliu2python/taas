# pylint: disable=no-name-in-module
import os

from flask import request, current_app
from flask_restful import Resource

from qaportal.clients.jenkins import JenkinsClient
from rest import RestApi

rest = RestApi(base_route="/qaportal")


@rest.route("/ready")
class Readiness(Resource):
    def get(self):
        return "Ready"


@rest.route("/healthz")
class Liveness(Resource):
    def get(self):
        return "Healthy"


@rest.route("/build/<string:job_name>")
class TriggerBuild(Resource):
    """
    POST /qaportal/build/<job_name>
    Triggers a Jenkins job. Returns the queue‐item URL (
    where you can poll for when it becomes a real build).
    Optional JSON body: { "param1": "value1", "param2": "value2" }
     if your job needs parameters.
    """
    def post(self, job_name):
        j_base = current_app.config['JENKINS_BASE_URL']
        j_user = current_app.config['JENKINS_USER']
        j_token = current_app.config['JENKINS_API_TOKEN']

        jc = JenkinsClient(base_url=j_base, username=j_user, api_token=j_token)

        # Read optional JSON body for parameters
        params = request.get_json(silent=True) or None

        try:
            queue_url = jc.build_job(job_name, params=params)
            return {'queue_url': queue_url}, 202
        except Exception as e:
            return {'error': str(e)}, 500


@rest.route("/results/<string:job_name>")
class GetResOfQATest(Resource):
    """
    GET /qaportal/results/<job_name>
    Fetches the latest build's JSON details for that Jenkins job.
    """
    def get(self, job_name):
        j_base = current_app.config['JENKINS_BASE_URL']
        j_user = current_app.config['JENKINS_USER']
        j_token = current_app.config['JENKINS_API_TOKEN']

        jc = JenkinsClient(base_url=j_base, username=j_user, api_token=j_token)

        try:
            build_info = jc.get_latest_build_info(job_name)
            # You might want to filter only the fields you care about.
            # For demonstration, return the full JSON that Jenkins returns.
            return build_info, 200
        except Exception as e:
            return {'error': str(e)}, 404
