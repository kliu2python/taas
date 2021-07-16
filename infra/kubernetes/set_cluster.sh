sudo swapoff -a
kubeadm init --pod-network-cidr=192.168.0.0/16
#rm $HOME/.kube -rf
#mkdir -p $HOME/.kube
#sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
#sudo chown $(id -u):$(id -g) $HOME/.kube/config
#kubectl create -f https://docs.projectcalico.org/manifests/tigera-operator.yaml
#kubectl create -f https://docs.projectcalico.org/manifests/custom-resources.yaml
#kubectl taint nodes --all node-role.kubernetes.io/master-
kubectl get nodes -o wide
