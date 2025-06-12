# jenkins_client.py

import requests
from requests.auth import HTTPBasicAuth


class JenkinsClient:
    """
    Minimal Jenkins API client to:
      1. fetch a crumb (for CSRF protection),
      2. trigger a job (with or without parameters), and
      3. query the latest build information for a job.
    """

    def __init__(self, base_url: str, username: str, api_token: str):
        """
        :param base_url: e.g. "http://jenkins.example.com:8080"
        :param username: Jenkins username
        :param api_token: Jenkins API token (or password)
        """
        self.base_url = base_url.rstrip('/')  # strip trailing slash if present
        self.auth = HTTPBasicAuth(username, api_token)
        self.session = requests.Session()
        self.session.auth = self.auth

        # Fetch a CSRF crumb and configure the session to send it automatically:
        crumb_data = self._get_crumb()
        self.session.headers.update({
            crumb_data['crumbRequestField']: crumb_data['crumb']
        })

    def _get_crumb(self) -> dict:
        """
        Jenkins exposes a crumb endpoint to protect against CSRF.
        We GET /crumbIssuer/api/json to retrieve something like:
          { "crumbRequestField": "Jenkins-Crumb", "crumb": "abcd1234" }
        """
        url = f"{self.base_url}/crumbIssuer/api/json"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

    def build_job(self, job_name: str, params: dict = None) -> str:
        """
        Trigger a Jenkins job. If 'params' is provided, it will use
        the /buildWithParameters endpoint; otherwise /build.

        Returns:
          The full queue‐item URL (from the 'Location' header).
          You can poll that to see when it becomes a build number.
        """
        if params:
            url = f"{self.base_url}/job/{job_name}/buildWithParameters"
            resp = self.session.post(url, params=params)
        else:
            url = f"{self.base_url}/job/{job_name}/build"
            resp = self.session.post(url)

        # Jenkins normalizes: HTTP 201 Created + a 'Location' header pointing
        # at something like "http://jenkins.example.com:8080/queue/item/123/"
        resp.raise_for_status()
        return resp.headers.get('Location')

    def _get_queue_item_info(self, queue_item_url: str) -> dict:
        """
        Given a queue URL (like ".../queue/item/123/"), GET its JSON:
          queue_item_url + "api/json"
        You can inspect when "executable" appears,
         which gives you the build number.
        """
        if not queue_item_url.endswith('/'):
            queue_item_url = queue_item_url + '/'
        url = f"{queue_item_url}api/json"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

    def get_latest_build_info(self, job_name: str) -> dict:
        """
        1. Fetch job info via /job/{job_name}/api/json
        2. Look at 'lastBuild' → { "number": 15, "url": "..." }
        3. GET /job/{job_name}/{number}/api/json and return that JSON.
        """
        # 1. get job summary
        job_url = f"{self.base_url}/job/{job_name}/api/json"
        job_resp = self.session.get(job_url)
        job_resp.raise_for_status()
        job_data = job_resp.json()

        last_build = job_data.get('lastBuild')
        if not last_build:
            raise RuntimeError(f"Job '{job_name}' has no builds yet.")

        build_number = last_build['number']
        build_url = f"{self.base_url}/job/{job_name}/{build_number}/api/json"
        build_resp = self.session.get(build_url)
        build_resp.raise_for_status()
        return build_resp.json()
