cd /home/fortinet/.ca
# Create a key
echo "****************Creating a key*****************"
openssl genrsa -aes256 \
	      -out intermediate/private/$1.key.pem 2048

echo ""
echo ""
echo "****************Create csr*********************"
# Create Signing request
openssl req -config intermediate/openssl.cnf -key intermediate/private/$1.key.pem -new -sha256 -out intermediate/csr/$1.csr.pem
echo ""
echo ""
echo "****************Sign Cert**********************"
# Sign cert
openssl ca -config intermediate/openssl.cnf -extensions server_cert -days 3650 -notext -md sha256 -in intermediate/csr/$1.csr.pem -out intermediate/certs/$1.cert.pem

echo "****************copy out certs*****************"
outputs=/home/fortinet/generated_certs/$1
mkdir -p $outputs
cp intermediate/certs/$1.cert.pem $outputs
cp intermediate/certs/ca-chain.cert.pem $outputs
cp intermediate/private/$1.key.pem $outputs
