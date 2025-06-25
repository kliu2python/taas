import os

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


@rest.route("/groups")
class ListAllGroups(Resource):
    def get(self):
        """
        Returns a list of all jobs from the MongoDB database using MongoDBAPI.
        """
        try:
            # Fetch the jobs from the MongoDB using the MongoDBAPI client
            jobs = MongoDBAPI().get_all_groups()
            return jsonify({"results": jobs})
        except Exception as e:
            return jsonify({"error": "Error fetching job structure on DB"}), 500


@rest.route("/run/execute/ftm")
class ExecuteFTMJenkinsTask(Resource):
    def post(self):
        try:
            data = request.json
            res = runner.execute_run_task(data)
            return jsonify({"results": res})
        except Exception as e:
            return jsonify({"error": "Error fetching job structure on DB"}), 500


@rest.route("/run/ios/ftm")
class GetFTMIOSTaskRun(Resource):
    def get(self):
        try:
            results = MongoDBAPI().get_all_run_results("ftm_ios")
        except Exception:
            return "auth failed", 500
        return results, 200


@rest.route("/run/results/ios/ftm")
class GetFTMIOSTaskRunResults(Resource):
    def get(self):
        try:
            results = runner.fetch_run_details()
        except Exception:
            return "auth failed", 500
        return results, 200


@rest.route("/run/result/ios/ftm")
class GetFTMIOSTaskRunResult(Resource):
    def get(self):
        try:
            job_name = request.args.get("job_name")
            results = runner.fetch_run_res_using_build_num(job_name)
        except Exception:
            return "auth failed", 500
        return results, 200


@rest.route("/run/result/ios/ftm/delete")
class DeleteFTMiOSResult(Resource):
    def delete(self):
        try:
            job_name = request.args.get("job_name")
            results = runner.delete_run_result(job_name)
        except Exception:
            return "auth failed", 500
        return results, 200


@rest.route("/apk_images")
class ListAllAPKImages(Resource):
    def get(self):
        apk_dir = "/home/fortinet/apks"
        try:
            files = [f for f in os.listdir(apk_dir) if f.endswith('.apk') or
                     f.endswith('.ipa')]
            return jsonify(files)
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@rest.route("/apk_images")
class UploadAPKFile(Resource):
    def post(self):
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Accept only .apk and .ipa
        if not (file.filename.endswith('.apk')
                or file.filename.endswith('.ipa')):
            return jsonify({'error': 'Only .apk and .ipa files allowed'}), 400

        save_path = os.path.join('/home/fortinet/apks', file.filename)
        try:
            file.save(save_path)
            return jsonify({'message': f'File {file.filename} successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
