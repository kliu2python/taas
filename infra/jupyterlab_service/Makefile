TAG_NAME := latest
DOCKER_IMAGE := 10.160.16.60/jupyterlab/jupyterlab_no_kernel:$(TAG_NAME)

all: push_docker_image

build_docker_image: 
	docker build -t $(DOCKER_IMAGE) .

push_docker_image: build_docker_image
	docker push $(DOCKER_IMAGE)

clean:
	docker system prune -a -f
