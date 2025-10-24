TAG_NAME := latest
REGISTERY := 10.160.16.60/uiux/portal
DOCKER_IMAGE := $(REGISTERY):$(TAG_NAME)

.PHONY: all build_docker_image push_docker_image frontend_install

all: build_docker_image

frontend_install:
	@npm install --prefix apps/frontend

build_docker_image:
	docker build -t $(DOCKER_IMAGE) .

push_docker_image: build_docker_image
	docker push $(DOCKER_IMAGE)
