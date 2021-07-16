FROM python:3.8.6-alpine3.11

COPY . /scaling_ui

WORKDIR /scaling_ui

RUN pip3 install --no-cache-dir -r requirements

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
