FROM python:3.7.12-alpine3.14

COPY . /taascli
RUN pip3 install --no-cache-dir -e /taascli
RUN mkdir /root/.taas
COPY taas.conf /root/.taas
CMD ["taas"]
