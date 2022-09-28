FROM python:3.8.14-slim-bullseye

COPY . /taas

WORKDIR /taas

RUN pip3 install --no-cache-dir -r baserequirements
RUN pip3 install --no-cache-dir -r requirements

CMD ["sh", "docker_run.sh"]
