FROM python:3.8.12-alpine3.14

COPY . /idplogin
RUN cd /idplogin
RUN pip install --no-cache-dir -r /idplogin/requirements
WORKDIR /idplogin

CMD ["python3", "run.py"]
