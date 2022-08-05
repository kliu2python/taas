FROM python:3.8.13-alpine3.16

COPY . /taas

RUN pip3 install --no-cache-dir -r /taas/baserequirements
RUN pip3 install --no-cache-dir -r /taas/requirements

RUN /bin/rm /bin/cat
RUN /bin/rm /usr/bin/vi
RUN /bin/rm /sbin/apk

ENTRYPOINT rq worker --path /taas --url $REDIS_URL
#ENTRYPOINT ["sh", "/taas/docker_run.sh"]
