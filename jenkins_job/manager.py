import json
import threading
from datetime import datetime
from time import sleep

import jenkins
import pika
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import aiohttp
import urllib.parse


import requests
from requests.auth import HTTPBasicAuth

from utils.MongoDBAPI import MongoDBAPI
from utils.logger import get_logger
from jenkins_job.conf import (
    CONF,
    QUEUE_NAME
)

logger = get_logger()

# Load configuration
jenkins_info = CONF.get("jenkins_info", {})
jobs_info = CONF.get("jobs_type", {})
JENKINS_IP = jenkins_info.get("ip")
JENKINS_UN = jenkins_info.get("username")
JENKINS_PW = jenkins_info.get("password")
job_paths = jenkins_info.get("jobs", {})


def extract_job_path(full_url: str) -> str:
    """Convert full Jenkins job URL to job path used by Jenkins API."""
    parsed = urllib.parse.urlparse(full_url)
    segments = parsed.path.strip('/').split('/')
    # Keep only job names (skip the 'job' keywords)
    job_parts = [segments[i + 1] for i in range(0, len(segments), 2) if
                 segments[i] == 'job']
    return '/'.join(job_parts)


class JenkinsJobs:
    def __init__(self, server_ip=JENKINS_IP, server_un=JENKINS_UN,
                 server_pw=JENKINS_PW):
        self.server = jenkins.Jenkins(
            server_ip, username=server_un, password=server_pw
        )
        self.mongo_client = MongoDBAPI()
        try:
            self.version = self.server.get_version()
            logger.info("Connected to Jenkins version: %s", self.version)
        except Exception as e:
            logger.error("Error connecting to Jenkins: %s", e)
            exit(1)

    def get_all_category(self, _type: str):
        job_path = jobs_info.get(_type)
        job_category_list = []
        if not job_path:
            logger.info(f"the job path of type {_type} is empty, check again.")
            return job_category_list
        for path in job_path:
            job_obj = self.server.get_job_info(path).get("jobs", [])
            for job in job_obj:
                job_category_list.append(job.get("name"))
        return job_category_list

    def _get_build_status(self, job_path, build_number):
        build_details = self.server.get_build_info(job_path, build_number)
        if build_details.get("building"):
            status = "BUILDING"
        else:
            status = build_details.get("result") or "UNKNOWN"
        return {
            "build_number": build_number,
            "build_status": status,
            "allure_url": "{}allure".format(build_details.get("url")),
        }

    def fetch_auth_info_by_job_name(self, job_name):
        job_info = self.mongo_client.get_job_by_name(job_name)
        return job_info

    def get_all_jobs(self, category: str = None, job_path: str = None):
        build_numbers = []
        if not job_path:
            job_path = job_paths.get(category)
        if not job_path:
            logger.error("No job path found for category: %s", category)
            return []
        job_path = job_path.rstrip("/")
        try:
            job_info = self.server.get_job_info(job_path)
            builds = job_info.get("builds", [])
            if not builds:
                logger.info("No builds found for job %s", job_path)
                return []
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_build = {
                    executor.submit(
                        self._get_build_status, job_path, build["number"]
                    ): build
                    for build in builds
                }
                for future in as_completed(future_to_build):
                    try:
                        build_status = future.result()
                        build_numbers.append(build_status)
                    except Exception as exc:
                        logger.error("Error processing a build: %s", exc)
            return build_numbers
        except jenkins.NotFoundException:
            logger.error("The job was not found. Please check the job path.")
        except Exception as e:
            logger.error("An error occurred: %s", e)

    def get_build_res(self, build_number: str,
                      category: str = "iPhone8-ios16"):
        job_path = job_paths.get(category)
        if not job_path:
            logger.error("No job path found for category: %s", category)
            return None
        job_path = job_path.rstrip("/")
        try:
            build_number_int = int(build_number)
            build_details = self.server.get_build_info(
                job_path, build_number_int
            )
            if build_details.get("building"):
                status = "BUILDING"
            else:
                status = build_details.get("result") or "UNKNOWN"
            return {
                "build_number": build_number,
                "build_status": status,
                "allure_url": "{}allure".format(build_details.get("url")),
            }
        except jenkins.NotFoundException:
            logger.error("Build %s not found in job %s", build_number, job_path)
            return None
        except Exception as e:
            logger.error(
                "An error occurred while retrieving build %s: %s",
                build_number, e
            )
            return None

    @classmethod
    def list_all_jobs_recursive(cls):
        async def list_jobs(session, base_path=""):
            if not base_path:
                url = "{}/api/json?tree=jobs[name,url,_class]".format(
                    JENKINS_IP
                )
            else:
                segments = [
                    "job/{}".format(urllib.parse.quote(part))
                    for part in base_path.split("/")
                ]
                job_segments = "/".join(segments)
                url = "{}/{}/api/json?tree=jobs[name,url,_class]".format(
                    JENKINS_IP, job_segments
                )
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()
            except Exception as e:
                logger.error("Error fetching URL %s: %s", url, e)
                return []
            jobs = data.get("jobs", [])
            full_paths = []
            tasks = []
            for job in jobs:
                full_path = (
                    job["name"]
                    if not base_path
                    else "{}/{}".format(base_path, job["name"])
                )
                full_paths.append(full_path)
                if "Folder" in job.get("_class", ""):
                    tasks.append(list_jobs(session, full_path))
            if tasks:
                for sub_list in await asyncio.gather(
                        *tasks, return_exceptions=True):
                    if isinstance(sub_list, list):
                        full_paths.extend(sub_list)
            return full_paths

        async def main():
            auth = aiohttp.BasicAuth(JENKINS_UN, JENKINS_PW)
            async with aiohttp.ClientSession(auth=auth) as session:
                return await list_jobs(session, "")

        try:
            all_jobs = asyncio.run(main())
            return all_jobs
        except Exception as e:
            logger.error("Error running async job listing: %s", e)

    def get_all_saved_jobs(self):
        res = self.mongo_client.get_all_jobs()
        return res

    def delete_saved_jobs(self, name):
        res = self.mongo_client.delete_job_by_name(name)
        return res

    def get_one_saved_job(self, name):
        res = self.mongo_client.get_job_by_name(f"name={name}")
        return res

    def get_job_parameters(self, job_path: str):
        """
        Fetches parameter definitions from a Jenkins job, if it is parameterized
        :param job_path: Full Jenkins job path
        :return: List of parameters (name, default, type, description)
        """
        try:
            job_info = self.server.get_job_info(job_path)
            parameters = []
            if job_info.get("property"):
                for prop in job_info.get("property", []):
                    param_defs = prop.get("parameterDefinitions")
                    if param_defs:
                        for param in param_defs:
                            tmp_type = param.get("_class") or param.get("type")
                            parameters.append({
                                "name": param.get("name"),
                                "type": tmp_type,
                                "default": param.get("defaultParameterValue",
                                                     {}).get("value"),
                                "description": param.get("description", "")})
            else:
                parameters = self.get_job_parameters_via_property(job_path)
            if parameters:
                logger.info("Fetched %d parameters for job %s", len(parameters),
                            job_path)
            else:
                logger.info("Job %s has no parameters", job_path)
            return parameters
        except jenkins.NotFoundException:
            logger.error("Job not found: %s", job_path)
        except Exception as e:
            logger.error("Failed to fetch parameters for job %s: %s", job_path,
                         e)
        return []

    @classmethod
    def get_job_parameters_via_property(cls, job_path: str):
        """
        Fetches job parameters from the `property` array
        """
        segments = [f"job/{part}" for part in job_path.strip("/").split("/")]
        url = f"{JENKINS_IP}/{'/'.join(segments)}/api/json"

        try:
            response = requests.get(
                url,
                auth=HTTPBasicAuth(JENKINS_UN, JENKINS_PW)
            )
            response.raise_for_status()
            data = response.json()
            tmp = "hudson.model.ParametersDefinitionProperty"

            for prop in data.get("property", []):
                if prop.get("_class") == tmp:
                    param_defs = prop.get("parameterDefinitions", [])
                    return [
                        {
                            "name": p.get("name"),
                            "type": p.get("type"),
                            "default": p.get(
                                "defaultParameterValue", {}
                            ).get("value"),
                            "description": p.get("description", ""),
                            "choices": p.get("choices", [])
                        } for p in param_defs]
            logger.info("No parameters found for job %s", job_path)
            return []

        except Exception as e:
            logger.error(
                "Error fetching job parameters from property for job %s: %s",
                job_path, e)
            return []

    def execute_job(self, body):
        job_name = extract_job_path(body.get("server_ip"))
        parameters = body.get("parameters")
        build_num = self.server.build_job(job_name, parameters)

        # Background worker function
        def update_build_info():
            while True:
                queue_info = self.server.get_queue_item(build_num)
                if 'executable' in queue_info:
                    build_url = queue_info['executable']['url']
                    build_number = queue_info['executable']['number']
                    job_info = self.get_one_saved_job(body.get("job_name"))
                    job_info["documents"][0]["parameters"] = parameters
                    job_info["documents"][0]["job_name"] = body.get("job_name")
                    builds = job_info.get("builds", {})
                    builds[build_num] = {
                        "build_num": build_number,
                        "build_url": build_url,
                        "res": "running"
                    }
                    job_info["documents"][0]["builds"] = builds
                    self.mongo_client.update_document(
                        job_info,
                        db_filter=f"name={body.get('job_name')}"
                    )
                    logger.info(f'saved the docs {job_info}')
                    break
                sleep(2)

        # Launch background thread
        threading.Thread(target=update_build_info, daemon=True).start()

        return True

    def fetch_build_res_using_build_num(self, job_path, build_number, job_name):
        """
        SUCCESS	    Build completed successfully
        FAILURE	    Build failed
        ABORTED	    Build was manually aborted
        UNSTABLE	Build succeeded but had test failures or unstable results
        NOT_BUILT	Build was never run (e.g. skipped)
        null	    Build is still running (not yet completed)
        """
        db_res = self.mongo_client.get_res_of_build_number(job_name,
                                                           build_number)
        if db_res in ["SUCCESS", "ABORTED", "FAILURE", "UNSTABLE", "NOT_BUILT"]:
            logger.info(f"fetch the res {db_res} from db")
            return db_res
        build_info = self.server.get_build_info(job_path, build_number)
        result = build_info.get('result')
        logger.info(f"the res of build {build_number} of job {job_path} is"
                    f" {result}")
        if result:
            self.mongo_client.update_jenkins_build_res(result, job_name,
                                                       build_number)

        return result

    @classmethod
    def submit_job_task(cls, job_name: str, parameters: dict):
        """
        Publishes a task to RabbitMQ to start a Jenkins build.
        This method accepts a job name (the full job URL or name)
        and a dictionary of parameters. It returns quickly to the API.
        """
        task = {"job_name": job_name, "parameters": parameters}
        con_url = CONF.get("rabbitmq")
        if not con_url:
            logger.error("RabbitMQ connection URL must be specified")
            return False
        try:
            connection = pika.BlockingConnection(
                pika.URLParameters(con_url)
            )
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            message = json.dumps(task)
            channel.basic_publish(
                exchange="",
                routing_key=QUEUE_NAME,
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            connection.close()
            logger.info("Submitted job task to queue: %s", message)
            return True
        except Exception as e:
            logger.error("Error submitting job task: %s", e)
            return False

    def execute_job_task(self, job_name: str, parameters: dict, udid: str):
        """
        Executes a Jenkins build with the given job name and parameters.
        Also saves the execution record into MongoDB using the provided
        udid as the primary key.
        """
        try:
            self.server.build_job(job_name, parameters=parameters)
            logger.info("Executed job %s with parameters %s", job_name,
                        parameters)
            record = {
                "_id": udid,  # Use the udid as the primary key.
                "job_name": job_name,
                "parameters": parameters,
                "status": "running",
                "started_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            if self.mongo_client:
                self.mongo_client.insert_document(record)
                logger.info("Saved execution record to MongoDB with udid: %s",
                            udid)
            else:
                logger.error(
                    "MongoDB client not initialized; record not saved.")
            return True
        except Exception as e:
            logger.error("Error executing job %s: %s", job_name, e)
            return False

    def update_job_status(self, udid: str, new_status: str):
        """
        Updates the execution record in MongoDB for the given udid.
        """
        if not self.mongo_client:
            logger.error("MongoDB client is not initialized.")
            return False
        try:
            result = self.mongo_client.update_document({"_id": udid}, {
                "$set": {"status": new_status,
                         "updated_at": datetime.utcnow()}})
            if result.modified_count:
                logger.info("Updated job %s status to %s", udid, new_status)
                return True
            else:
                logger.info("No update performed for job %s", udid)
                return False
        except Exception as e:
            logger.error("Error updating job %s: %s", udid, e)
            return False

    def generate_saved_jobs(self, body):
        if not body.get('job_name'):
            return 'missing job name', 400
        server_ip = body.get('server_ip')
        server_un = body.get('server_un')
        server_pw = body.get('server_pw')
        job_path = body.get('job_path')
        parameters_entry = body.get('parameters_entry')

    def fetch_job_structure(self, data):
        job_path = data.get('server_ip')
        job_name = data.get('job_name')
        server_un = data.get("server_un")
        server_pw = data.get("server_pw")
        api_url = f"{job_path.rstrip('/')}/api/json"
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            tmp_target = "hudson.model.ParametersDefinitionProperty"
            for prop in data.get("property", []):
                if prop.get("_class") == tmp_target:
                    res = [
                        {"name": p.get("name"),
                         "type": p.get("type"),
                         "default": p.get("defaultParameterValue", {}).get("value"),
                         "description": p.get("description", ""),
                         "choices": p.get("choices", [])} for p in
                        prop.get("parameterDefinitions", [])]
                    record = {
                        "name": job_name,
                        "server_ip": job_path,
                        "server_un": server_un,
                        "server_pw": server_pw,
                        "parameters": res
                    }
                    self.mongo_client.update_document(
                        record,  db_filter=f"name={job_name}"
                    )
                    return res

            return []  # no parameters defined
        except Exception as e:
            print(f"Failed to fetch parameters: {e}")
            return []

    def fetch_and_store_job_structure(self, job_path: None):
        """
        Fetch the job structure from Jenkins
        and store it as nested JSON in MongoDB.
        """
        async def list_jobs(session, base_path=""):
            if base_path:
                segments = [f"job/{urllib.parse.quote(part)}" for part in
                            base_path.split("/")]
                job_segments = "/".join(segments)
                url = (f"{JENKINS_IP}/{job_segments}"
                       f"/api/json?tree=jobs[name,url,_class]")
            else:
                url = f"{JENKINS_IP}/api/json?tree=jobs[name,url,_class]"

            logger.info(f"Fetching URL: {url}")
            try:
                async with (
                    session.get(
                        url,
                        auth=aiohttp.BasicAuth(JENKINS_UN, JENKINS_PW)
                    )
                    as response
                ):
                    response.raise_for_status()
                    data = await response.json()
                    logger.info(f"Response received for {url}")
            except Exception as e:
                logger.error(f"Error fetching URL {url}: {e}")
                return []

            jobs = data.get("jobs", [])
            job_tree = []

            for job in jobs:
                job_name = job["name"]
                job_url = job.get("url") or (
                    f"{JENKINS_IP}/{'/'.join(['job/' + urllib.parse.quote(part) for part in (base_path + '/' if base_path else '').split('/') if part])}{job_name}/")
                node = {"name": job_name, "url": job_url, "children": []}

                # Construct full job path for reference
                full_path = f"{base_path}/{job_name}" if base_path else job_name

                if "Folder" in job.get("_class", ""):
                    # Recursively fetch children jobs
                    children = await list_jobs(session, base_path=(
                        f"{base_path}/{job_name}" if base_path else job_name))
                    node["children"] = children
                else:
                    # Only add job path if it's a leaf (non-folder) job
                    node["path"] = full_path

                job_tree.append(node)

            return job_tree

        async def main():
            async with aiohttp.ClientSession() as session:
                return await list_jobs(session)

        try:
            all_jobs_tree = asyncio.run(main())
            logger.info(
                f"Fetched job tree with {len(all_jobs_tree)} top-level jobs.")

            # Store the entire nested job tree in MongoDB as one document
            self.store_job_structure_in_db(all_jobs_tree)

        except Exception as e:
            logger.error(f"Error running async job listing: {e}")

    def store_job_structure_in_db(self, job_tree_json):
        """
        Store the nested job structure JSON in the database as a single document
        """
        try:
            job_document = {
                "name": "10.160.13.30:8080",
                "jenkins_jobs_tree": job_tree_json
            }

            # Assuming `update_document` will upsert or insert the document
            inserted_job = self.mongo_client.update_document(
                job_document, db_filter="name=10.160.13.30:8080")

            if inserted_job:
                if inserted_job == 'no_update':
                    logger.info("No changes need to be updated")
                else:
                    logger.info("Nested job structure stored"
                                " successfully in the database.")
            else:
                logger.error(
                    "Failed to store nested job structure in the database.")

        except Exception as e:
            logger.error(f"Error storing job structure in DB: {e}")


# Example usage:
if __name__ == "__main__":
    runner = JenkinsJobs()
    # Example: Submit a task to RabbitMQ.
    sample_job = "mobile_test/FortiToken_Mobile/iOS/ios_job"
    sample_params = {"PARAM1": "value1", "PARAM2": "value2"}
    if runner.submit_job_task(sample_job, sample_params):
        logger.info("Task submitted successfully.")

