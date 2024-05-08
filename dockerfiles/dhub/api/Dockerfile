FROM python:3.8.19

COPY . /taas

WORKDIR /taas

RUN pip3 install --no-cache-dir -r requirements

CMD ["sh", "docker_run.sh"]
