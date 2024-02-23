FROM python:3.6.12-slim-buster

COPY . /taas

WORKDIR /taas

RUN pip3 install --no-cache-dir -r baserequirements \
    && pip3 install --no-cache-dir -r requirements

CMD ["sh", "docker_run.sh"]
