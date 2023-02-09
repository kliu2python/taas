FROM python:3.8.13-alpine3.16

COPY . /code

RUN pip install --no-cache-dir -r /code/requirements

WORKDIR /code
CMD ["sh", "docker_run.sh"]

