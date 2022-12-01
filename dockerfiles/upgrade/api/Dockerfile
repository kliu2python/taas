FROM python:3.8.13-alpine3.16

COPY . /taas

WORKDIR /taas
RUN apk add build-base libffi-dev openssl-dev \
    && pip3 install --no-cache-dir -r baserequirements \
    && pip3 install --no-cache-dir -r requirements \
    && apk del build-base libffi-dev openssl-dev \
    && /bin/rm /bin/cat \
    && /bin/rm /usr/bin/vi \
    && /bin/rm /sbin/apk
CMD ["sh", "docker_run.sh"]
