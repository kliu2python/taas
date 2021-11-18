git clone https://github.com/apache/pulsar-helm-chart
cd pulsar-helm-chart
./scripts/pulsar/prepare_helm_release.sh -n pulsar -k pulsar -c
cd ..
helm repo add apache https://pulsar.apache.org/charts
helm repo update
helm upgrade --install --values pulsar_values.yaml pulsar apache/pulsar
