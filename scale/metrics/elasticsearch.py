import base64
import datetime
import re

import requests
from scale.common.constants import CONFIG_PATH
from utils.metrics import Metrics

ELASTICSEARCH_METRICS = {
    "elastic_search_ftc_api_duration": {
        "method": "get_data",
        "args": {"data_type": "duration"},
        "labels": ["api_name", "ftc_server", "client_ip", "version"],
        "description": "FTC Api Response Duration"
    },
    "elastic_search_ftc_api_response_code": {
        "method": "get_data",
        "args": {"data_type": "response_code"},
        "labels": ["api_name", "ftc_server", "client_ip", "version"],
        "description": "FTC Api Response code"
    }
}
uuid_patten = re.compile("^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}"
                         "-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


class ElasticSearchMixin:
    @classmethod
    def search(cls, query, elastic_search_server, credential: str):
        credential = base64.b64encode(credential.encode()).decode()
        res = requests.post(
            f"https://{elastic_search_server}/_search",
            json=query,
            headers={"Authorization": f"Basic {credential}"},
            verify=False
        )
        return res.json()


class ElasticSearchFtc(ElasticSearchMixin):
    def __init__(self, data):
        self.elastic_server = data.get("elastic_search_engine")
        self.credential = data.get("elastic_search_credential")
        self.data = data.get("elastic_search", {})
        self.constant_query = None
        self.last_check_time = datetime.datetime.utcnow().isoformat()
        self.queue = {"duration": [], "response_code": []}

    @property
    def ftc_api_query(self):
        if not self.constant_query:
            must = []
            client_ip = self.data.get("client_ip")
            if client_ip:
                must.append({"match": {"context.client_ip": client_ip}})
            ftc_server = self.data.get("ftc_server")
            if ftc_server:
                must.append({"match": {"host.name": ftc_server}})
            version = self.data.get("version")
            if version:
                must.append({"match": {"host.name": version}})
            must.extend(
                [
                    {"match": {"filename": "wsgi.py"}},
                    {"match_phrase_prefix": {"request_url": "/api/v1"}}
                ]
            )
            self.constant_query = must

        query = {
            "size": 10000,
            "query": {
                "bool": {
                    "must": self.constant_query,
                    "filter": [
                        {
                            "range": {
                                "@timestamp": {"gte": f"{self.last_check_time}"}
                            }
                        }
                    ]
                }
            }
        }
        return query

    @staticmethod
    def _get_api_name(url):
        if url and "/api/v1/" in url:
            urls = url.split("/")
            new_urls = []
            for u in urls:
                if u:
                    if uuid_patten.match(u):
                        to_append = "_uuid_"
                    elif "?" in u:
                        to_append = u.split("?")[0]
                        if uuid_patten.match(to_append):
                            to_append = "_uuid_"
                    else:
                        to_append = u
                    if to_append:
                        new_urls.append(to_append)
            url = "/".join(new_urls[2:])
        return url

    def get_data(self, data_type):
        if data_type in ["duration"]:
            query = self.ftc_api_query
            res = self.search(query, self.elastic_server, self.credential)

            for dt, _ in self.queue.items():
                max_value = {}
                for hit in res.get("hits", {}).get("hits", []):
                    hit = hit["_source"]
                    url = self._get_api_name(hit.get("request_url"))
                    ftc_server = hit.get("host", {}).get("name", "")
                    client_ip = hit.get("clientip", "")
                    action = hit.get("action", "")
                    version = hit.get("extra", {}).get("version", "")
                    key = [url, ftc_server, client_ip, action, version]
                    key = "|".join(key)
                    max_value[key] = max(
                        max_value.get(key, 0), hit[dt]
                    )

                for k, v in max_value.items():
                    url, ftc_server, client_ip, action, version = k.split("|")
                    d = {
                        "labels": {
                            "api_name": f"{url}:{action}",
                            "ftc_server": ftc_server,
                            "client_ip": client_ip,
                            "version": version
                        },
                        "value": v
                    }
                    self.queue[dt].append([d])
            self.last_check_time = datetime.datetime.utcnow().isoformat()
        if self.queue.get(data_type):
            return self.queue[data_type].pop(0)
        return []


class ElasticSearchMetrics(Metrics):
    def __init__(self, session_id, **data):
        elasticsearch = ElasticSearchFtc(data)
        super().__init__(
            ELASTICSEARCH_METRICS,
            f"{session_id}-elastic_search",
            elasticsearch,
            data.get("ftc_server"),
            config_path=CONFIG_PATH
        )
        self.start_async()


class ElasticSearchMonitor(Metrics):
    def __init__(self, **data):
        elasticsearch = ElasticSearchFtc(data)
        super().__init__(
            ELASTICSEARCH_METRICS,
            "ftc-api-elastic_search",
            elasticsearch,
            config_path=CONFIG_PATH
        )
