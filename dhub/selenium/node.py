import requests

from utils.logger import get_logger

URL = "http://10.160.24.17:32609/status"
logger = get_logger()


class Node:
    def __init__(self, os: dict = None, availability: str = None, browser: dict = None):
        self.os = os
        self.availability = availability
        self.browser = browser


def _call_api_client():
    node_list = []
    try:
        response = requests.get(URL)
        if response.status_code == 200:
            # Successful GET request
            logger.info("The fetch data of selenium node successfully.")
            res = response.json()
            for node in res.get("value").get("nodes"):
                cur_node = {"os": node.get("osInfo"), "status": node.get("availability"), "browser_info": node.get("slots")[0].get("stereotype")}
                node_list.append(cur_node)
            return node_list
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")


def get_nodes():
    return _call_api_client()
