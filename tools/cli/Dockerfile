FROM python:3.7.12-alpine3.14

COPY . /taas-cli-client
RUN pip3 install --no-cache-dir -e /taas-cli-client
RUN mkdir /root/.taas
COPY taas.conf /root/.taas
CMD ["taas"]
