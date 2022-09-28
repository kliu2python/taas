import ast
import json
import os

import requests
import yaml
from flask_restful import Resource, request

from rest import RestApi
from k8s.conf import CONF

rest = RestApi(base_route="/k8s/v1/")

KUBE_FILE_PATH = os.path.dirname(os.path.dirname(__file__))


@rest.route("deploy")
class Deploy(Resource):
    """
    {
      "namespace": "para";
      "replicas": "para"

      change the parameters inside env to parameters, inside "env"
      "env": {
      "CONCURRENT": "para";
      "REPEAT": "para";
      "AUTHMODE": "para";
      "NAAS_SSL_CERT": "/"+"para";
      "NAAS_SSL_KEY":  "/"+"para"
      }
    }
    """

    def post(self):
        config_download_server = CONF.get(
            "config_download_server", "10.160.50.118:8889"
        )
        input_data = request.data.decode()
        input_data = ast.literal_eval(input_data)
        # Process and deserialize the data
        input_data.replace("\\n", "")
        input_data.replace("\\", "")
        input_data.replace("\n", "")
        input_data = json.loads(input_data)

        # Set the default value
        replica = input_data.get("replicas", 1)
        namespace = input_data.get("namespace", "default-perf-runner")

        kube_file = os.path.join(
            KUBE_FILE_PATH, f"kube_file_{namespace}.yaml"
        )

        if os.path.exists(kube_file):
            os.remove(kube_file)

        template_data = requests.get(
            f"http://{config_download_server}/"
            f"runner_naas.yaml"
        )

        # return data
        kube_content = list(
            yaml.safe_load_all(template_data.content.decode("utf-8"))
        )

        for content in kube_content:
            if content.get("kind") in ["Namespace"]:
                if namespace:
                    content["metadata"]["name"] = namespace
            if content.get("kind") in ["Deployment"]:
                if namespace:
                    content["metadata"]["namespace"] = namespace
                content["spec"]["replicas"] = replica
                containers = content["spec"]["template"]["spec"]["containers"]
                temp_dict = input_data.pop("env", {})
                for c in containers:
                    for key, value in temp_dict.items():
                        c["env"].append({"name": key, "value": value})

                if "command" not in containers:
                    containers[0]["command"] = ["/bin/bash"]
                if "args" not in containers:
                    containers[len(containers) - 1]["args"] = [
                        "-c",
                        "wget http://10.160.50.118:8889/fgt_b.crt;"
                        "wget http://10.160.50.118:8889/fgt_b.key;"
                        "./authclient"
                    ]
            with open(kube_file, "w") as FILE:
                yaml.safe_dump_all(kube_content, FILE)
        os.system(f"kubectl apply -f {kube_file}")
