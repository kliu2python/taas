FROM python:3.8.13-alpine3.16

COPY . /taas

WORKDIR /taas
RUN apk add build-base libffi-dev openssl-dev
RUN pip3 install --no-cache-dir -r baserequirements
RUN pip3 install --no-cache-dir -r requirements
RUN apk del build-base libffi-dev openssl-dev
CMD ["sh", "docker_run.sh"]
