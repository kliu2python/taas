import os
import socket

from saml2.assertion import Policy
import saml2.xmldsig as ds


host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)


HOST = host_ip
PORT = int(os.environ["BASE_PORT"])
HTTPS = True
SIGN_ALG = None
DIGEST_ALG = None
#SIGN_ALG = ds.SIG_RSA_SHA512
#DIGEST_ALG = ds.DIGEST_SHA512

# Which groups of entity categories to use
POLICY = Policy(
    {
        "default": {"entity_categories": ["swamid", "edugain"]}
    }
)

# HTTPS cert information
SERVER_CERT = "pki/cert.pem"
SERVER_KEY = "pki/key.pem"
CERT_CHAIN = ""
