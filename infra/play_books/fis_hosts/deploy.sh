export ANSIBLE_HOST_KEY_CHECKIN=False
ansible-playbook -i hosts node_exporter.yaml -K #--ask-pass
ansible hosts -i hosts -m shell -a "systemctl status prometheus_node_exporter.service | grep Active:" #--ask-pass
