TAG_NAME := latest
REGISTERY := 10.160.16.60/infra/dns
DOCKER_IMAGE := $(REGISTERY):$(TAG_NAME)

all: build

build:
	docker build -t $(DOCKER_IMAGE) .

push: build
	docker push $(DOCKER_IMAGE)
