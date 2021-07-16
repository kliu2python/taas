#!/bin/bash
cd /shared_folder/.ca
# Create a key
CERT_TYPE=${2:-both}
echo "Generating $CERT_TYPE for $1"
echo "****************Creating a key*****************"
openssl genrsa -out intermediate/private/$1.key.pem 2048

echo ""
echo ""
echo "****************Create csr*********************"
# Create Signing request
openssl req -config intermediate/openssl_docker.cnf -key intermediate/private/$1.key.pem -new -sha256 -out intermediate/csr/$1.csr.pem
echo ""
echo ""
echo "****************Sign Cert**********************"
# Sign cert
openssl ca -config intermediate/openssl_docker.cnf -extensions $CERT_TYPE -extfile ext_$CERT_TYPE.cnf -days 3650 -notext -md sha256 -in intermediate/csr/$1.csr.pem -out intermediate/certs/$1.cert.pem

echo "****************copy out certs*****************"
outputs=/shared_folder/$1
mkdir -p $outputs
cp intermediate/certs/$1.cert.pem $outputs
cp intermediate/certs/ca-chain.cert.pem $outputs
cp intermediate/private/$1.key.pem $outputs
