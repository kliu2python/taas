import json
import urllib

import requests

from utils.logger import get_logger

logger = get_logger()


class MongoDBAPI:
    def __init__(self,
                 api_base="http://10.160.24.88:31742/api/v1/mongodb/document",
                 db_name="jenkins",
                 collection="jobs"):
        """
        :param api_base:   REST endpoint root, e.g.
                           "http://host:port/api/v1/mongodb/document"
        :param db_name:    the database to use
        :param collection: the collection to use
        """
        self.api_base = api_base.rstrip('/')
        self.db = db_name
        self.collection = collection

    def _url(self, action: str) -> str:
        return f"{self.api_base}/{action}"

    def insert_document(self, document):
        """Insert a document into the MongoDB collection."""
        url = self._url(f"insert?db={self.db}&collection={self.collection}")
        try:
            response = requests.post(url, json=document)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error inserting document into MongoDB: {e}")
            return None

    def update_document(self, document, db_filter=None):
        if db_filter:
            # Step 1: Convert filter dict to JSON string
            filter_json = json.dumps(db_filter)

            # Step 2: URL-encode the JSON string
            encoded_filter = urllib.parse.quote(filter_json)

            # Step 3: Compose the URL safely
            get_url = self._url(
                f"find?db={self.db}"
                f"&collection={self.collection}&filter={encoded_filter}"
            )

            get_response = requests.get(get_url)
            if len(get_response.json().get("documents")) > 0:
                transformed_filter = db_filter
                if document.get("jenkins_jobs_tree") == get_response.json().get(
                        "documents")[0].get("jenkins_jobs_tree"):
                    return "no_update"
                if isinstance(db_filter, str) and "=" in db_filter:
                    key, value = db_filter.split("=", 1)
                    transformed_filter = {key.strip(): value.strip()}
                elif not isinstance(db_filter, dict):
                    raise Exception("db_filter is incorrect.")
                update_body = {
                    "filter": transformed_filter,
                    "update": {"$set": document}
                }
                url = self._url(
                    f"update?db={self.db}&collection={self.collection}")
                response = requests.put(url, json=update_body)
            else:
                url = self._url(f"insert?db={self.db}&collection"
                                f"={self.collection}")
                response = requests.post(url, json=document)
        else:
            url = self._url(f"insert?db={self.db}&collection"
                            f"={self.collection}")
            response = requests.post(url, json=document)
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error inserting document into MongoDB: {e}")
            return None

    def get_all_jobs(self):
        """Fetch all job names from the MongoDB collection."""
        url = self._url("find?db=jenkins&collection=jobs")
        try:
            response = requests.get(url)
            response.raise_for_status()  # Will raise an error for HTTP errors
            data = response.json()
            # Assuming that data contains a list of job names
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching jobs from MongoDB: {e}")
            return []

    def get_job_by_name(self, name):
        """Fetch all job names from the MongoDB collection."""
        filter_json = json.dumps(name)

        # Step 2: URL-encode the JSON string
        encoded_filter = urllib.parse.quote(filter_json)
        url = self._url(f"{self.db}/{self.collection}/find?"
                        f"db=jenkins&collection=jobs&filter={encoded_filter}")
        try:
            response = requests.get(url)
            response.raise_for_status()  # Will raise an error for HTTP errors
            data = response.json()
            # Assuming that data contains a list of job names
            return [job['parameters'] for job in data]
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching jobs from MongoDB: {e}")
            return []
