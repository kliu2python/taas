TAG_NAME := latest
REGISTERY := 10.160.16.60/taas/test_assistant
DOCKER_IMAGE := $(REGISTERY):$(TAG_NAME)

all: build_docker_image

build_docker_image:
	docker build -t $(DOCKER_IMAGE) .

push_docker_image: build_docker_image
	docker push $(DOCKER_IMAGE)
