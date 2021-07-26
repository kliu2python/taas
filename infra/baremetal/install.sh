#!/bin/bash

set +e

docker pull 10.160.16.60/taas-baremetal/scale-controller
docker pull 10.160.16.60/taas-baremetal/scale-worker
docker pull 10.160.16.60/taas-baremetal/scale-api
docker pull redis:alpine3.14
docker pull prom/pushgateway

docker kill  scale-controller scale-session-worker scale-metrics-worker scale-api scale-cache
docker rm scale-controller scale-session-worker scale-metrics-worker scale-api scale-cache

docker run -d --name scale-cache -p 6379:6379 redis:alpine3.14
docker run -d --name scale-push-gateway -p 9091 prom/pushgateway
docker run -d --name scale-controller --net=host 10.160.16.60/taas-baremetal/scale-controller
docker run -d --name scale-session-worker --net=host 10.160.16.60/taas-baremetal/scale-worker
docker run -d --name scale-metrics-worker --net=host -e WORKER_TYPE=metrics 10.160.16.60/taas-baremetal/scale-worker
docker run -d --name scale-api --net=host 10.160.16.60/taas-baremetal/scale-api