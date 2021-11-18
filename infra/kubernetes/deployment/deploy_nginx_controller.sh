git clone https://github.com/nginxinc/kubernetes-ingress/
cd kubernetes-ingress/deployments
git checkout v1.8.1

kubectl apply -f common/ns-and-sa.yaml
kubectl apply -f rbac/rbac.yaml
kubectl apply -f rbac/ap-rbac.yaml

kubectl apply -f common/default-server-secret.yaml
kubectl apply -f common/nginx-config.yaml
kubectl apply -f common/vs-definition.yaml
kubectl apply -f common/vsr-definition.yaml
kubectl apply -f common/ts-definition.yaml
kubectl apply -f common/policy-definition.yaml

kubectl apply -f common/gc-definition.yaml
kubectl apply -f common/global-configuration.yaml

#kubectl apply -f deployment/nginx-ingress.yaml

## Make sure add following to DaemonSet config:
# - -global-configuration=$(POD_NAMESPACE)/nginx-configuration

kubectl apply -f daemon-set/nginx-ingress.yaml

#kubectl create -f service/nodeport.yaml

kubectl get pods --namespace=nginx-ingress

