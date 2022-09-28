FROM python:3.6.12-slim-buster

COPY . /test_assistant_rest_api
COPY kubeconfig /root/.kube/config

WORKDIR /test_assistant_rest_api

RUN pip3 install --no-cache-dir -r requirements
RUN pip3 install --no-cache-dir -r baserequirements

RUN apt update && apt install -y curl git && rm -rf /var/lib/apt/lists/*

RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.20.0/bin/linux/amd64/kubectl
RUN chmod u+x kubectl && mv kubectl /bin/kubectl

CMD ["bash", "docker_run.sh"]
