FROM python:3.8.12-slim-buster

COPY . /sp-wsgi
WORKDIR /sp-wsgi
RUN pip install --no-cache-dir -r requirements
RUN cp to_replace/response.py /usr/local/lib/python3.8/site-packages/saml2
RUN cp to_replace/wsgi.py /usr/local/lib/python3.8/site-packages/cheroot

RUN apt update
RUN apt install -y xmlsec1 wget
RUN apt clean

CMD ["sh", "start.sh"]
