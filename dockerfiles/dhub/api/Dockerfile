FROM python:3.10.14

COPY . /taas

WORKDIR /taas

RUN apt reinstall python3-requests \
    && pip3 install --no-cache-dir -r requirements

CMD ["sh", "docker_run.sh"]
