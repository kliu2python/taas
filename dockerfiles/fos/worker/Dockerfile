FROM python:3.8.13-alpine3.16

COPY . /taas

RUN apk add build-base
RUN pip3 install --no-cache-dir -r baserequirements
RUN pip3 install --no-cache-dir -r requirements
RUN apk del build-base

RUN /bin/rm /bin/cat
RUN /bin/rm /usr/bin/vi
RUN /bin/rm /sbin/apk

ENTRYPOINT rq worker --path /taas --url $REDIS_URL
#ENTRYPOINT ["sh", "/taas/docker_run.sh"]
