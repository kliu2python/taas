FROM python:3.10.15-slim-bullseye

COPY . /taas

WORKDIR /taas

RUN pip3 install --no-cache-dir -r baserequirements \
    && pip3 install --no-cache-dir -r requirements

CMD ["sh", "docker_run.sh"]
