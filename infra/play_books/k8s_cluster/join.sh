export ANSIBLE_HOST_KEY_CHECKIN=False
ansible-playbook -i hosts join_cluster.yaml --extra-vars="master_ip=10.0.2.55 bootstrap_token=z5bo9h.pgbzs190skwkv3dn"
