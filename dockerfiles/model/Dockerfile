FROM python:3.6.12-slim-buster

COPY . /test_assistant_rest_api

WORKDIR /test_assistant_rest_api

RUN pip3 install --no-cache-dir torch==1.6.0+cpu torchvision==0.7.0+cpu \
    -f https://download.pytorch.org/whl/torch_stable.html \
    && pip3 install --no-cache-dir -r baserequirements \
    && pip3 install --no-cache-dir -r requirements \
    && apt update && apt install -y wget && rm -rf /var/lib/apt/lists/*

CMD ["bash", "docker_run.sh"]
