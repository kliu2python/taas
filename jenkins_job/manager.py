import json
from datetime import datetime

import jenkins
import pika
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import aiohttp
import urllib.parse

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


class JenkinsJobs:
    def __init__(self):
        self.server = jenkins.Jenkins(
            JENKINS_IP, username=JENKINS_UN, password=JENKINS_PW
        )
        try:
            self.version = self.server.get_version()
            logger.info("Connected to Jenkins version: %s", self.version)
        except Exception as e:
            logger.error("Error connecting to Jenkins: %s", e)
            exit(1)

    def get_all_category(self, _type: str):
        job_path = jobs_info.get(_type)
        job_category_list = []
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
                self.mongo_collection.insert_one(record)
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
            result = self.mongo_collection.update_one({"_id": udid}, {
                "$set": {"status": new_status,
                         "updated_at": datetime.datetime.utcnow()}})
            if result.modified_count:
                logger.info("Updated job %s status to %s", udid, new_status)
                return True
            else:
                logger.info("No update performed for job %s", udid)
                return False
        except Exception as e:
            logger.error("Error updating job %s: %s", udid, e)
            return False

    def get_job_status(self, udid: str):
        """
        Retrieves the execution record from MongoDB using the udid as the
        primary key.
        """
        if not self.mongo_client:
            logger.error("MongoDB client is not initialized.")
            return None
        try:
            record = self.mongo_collection.find_one({"_id": udid})
            if record:
                logger.info("Found job record for udid %s: %s", udid, record)
                return record
            else:
                logger.info("No job found with udid: %s", udid)
                return None
        except Exception as e:
            logger.error("Error retrieving job with udid %s: %s", udid, e)
            return None


# Example usage:
if __name__ == "__main__":
    runner = JenkinsJobs()
    # Example: Submit a task to RabbitMQ.
    sample_job = "mobile_test/FortiToken_Mobile/iOS/ios_job"
    sample_params = {"PARAM1": "value1", "PARAM2": "value2"}
    if runner.submit_job_task(sample_job, sample_params):
        logger.info("Task submitted successfully.")

    # Later, a worker might call execute_job_task() after fetching the task.
    # runner.execute_job_task(sample_job, sample_params)
