FROM public.ecr.aws/sam/build-python3.8:latest

COPY . /jenkins

WORKDIR /jenkins

RUN pip3 install --no-cache-dir -r baserequirements \
    && pip3 install --no-cache-dir -r requirements

CMD ["bash", "docker_run.sh"]
