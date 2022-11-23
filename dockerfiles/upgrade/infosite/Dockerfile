FROM python:3.8.13-alpine3.16

COPY . /taas

WORKDIR /taas

WORKDIR /taas

RUN pip3 install --no-cache-dir -r requirements

RUN /bin/rm /bin/cat
RUN /bin/rm /usr/bin/vi
RUN /bin/rm /sbin/apk

ENTRYPOINT sh docker_run.sh
