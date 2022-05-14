export ANSIBLE_HOST_KEY_CHECKIN=False
ansible-playbook -i hosts adjust_max_pods.yaml --extra-vars="max_pods=1000"
