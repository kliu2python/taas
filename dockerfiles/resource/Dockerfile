FROM python:3.6.12-buster

COPY . /test_assistant_rest_api

WORKDIR /test_assistant_rest_api

RUN pip3 install --no-cache-dir -r baserequirements
RUN pip3 install --no-cache-dir -r requirements

CMD ["bash", "docker_run.sh"]
