FROM python:3.8.13-alpine3.16

COPY . /taas

WORKDIR /taas

RUN pip3 install --no-cache-dir -r requirements \
    && /bin/rm /bin/cat \
    && /bin/rm /usr/bin/vi \
    && /bin/rm /sbin/apk

ENTRYPOINT rq worker --path /taas --url $REDIS_URL
#ENTRYPOINT ["sh", "/taas/docker_run.sh"]
