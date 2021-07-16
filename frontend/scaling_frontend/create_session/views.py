from django.shortcuts import render
import requests
import json

# Create your views here.
from .forms import RequestForm
from lib.variables import create_url


def get_json_data(cleaned_data):
    body = {
        "session_id": cleaned_data["session_id"],
        "servers": [
            {
                "ssh_ip": cleaned_data["host_ip"],
                "ssh_user": cleaned_data["username"],
                "ssh_password": cleaned_data["password"],
                "target_server_ip": cleaned_data["target_host_ip"]
            }
        ],
        "target_platform": cleaned_data["target_platform"],
        "runner_count": eval(cleaned_data["runner_count"]),
        "loop": cleaned_data["loop"],
        "wait_seconds_after_notify": cleaned_data["wait_seconds_after_notify"],
        "deployment_config": cleaned_data["deployment_config"],
        "pods_adjust_momentum": cleaned_data["pods_adjust_momentum"],
        "force_new_session": cleaned_data["force_new_session"]
    }
    return json.dumps(body)


def send_create_session_request(data_json, url, params):
    try:
        r = requests.request("POST",
                             url,
                             data=data_json, params=params,
                             headers={'Content-Type': 'application/json'})
        res = r.json()
        if "results" in res.keys():
            if "FAIL" in res["results"]:
                return "FAIL"
            else:
                return res["results"]
        else:
            return "FAIL"
    except requests.exceptions.RequestException:
        return "connection_error"


def home_view(request, *args, **kwargs):
    message = ""
    assigned_session_id = ""
    if request.method == 'POST':
        form = RequestForm(request.POST)
        if form.is_valid():
            data_json = get_json_data(form.cleaned_data)
            res = send_create_session_request(data_json, create_url, {})
            if res == "connection_error":
                message = "ERROR"
            elif res == "FAIL":
                message = "FAIL"
            else:
                message = "SUCCESS"
                assigned_session_id = res
    else:
        form = RequestForm()
    dict = {
        "form": form,
        "message": message,
        "assigned_session_id": assigned_session_id
    }
    return render(request, "home.html", dict)
