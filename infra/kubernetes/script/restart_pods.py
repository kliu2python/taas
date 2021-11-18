from kubernetes import client, config

config.load_kube_config()
namespace = "scale-controller"
v1 = client.CoreV1Api()
ret = v1.list_namespaced_pod(namespace)
pods_to_kill = [
    "scale-controller",
    "scale-api",
    "scale-session-worker",
    "scale-metrics-worker",
    "scale-cache"
]
target = []


for pod in ret.items:
    pod_name = pod.metadata.name
    for name in pods_to_kill:
        if name in pod_name:
            print(f"killing pod {pod_name}")
            v1.delete_namespaced_pod(pod_name, namespace)
            break
