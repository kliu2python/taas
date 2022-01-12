import os

from saml2.entity_category.edugain import COC
from saml2 import BINDING_HTTP_REDIRECT
from saml2 import BINDING_HTTP_POST
from saml2.saml import NAME_FORMAT_URI

try:
    from saml2.sigver import get_xmlsec_binary
except ImportError:
    get_xmlsec_binary = None


if get_xmlsec_binary:
    xmlsec_path = get_xmlsec_binary(["/opt/local/bin", "/usr/local/bin"])
else:
    xmlsec_path = '/usr/local/bin/xmlsec1'

# Make sure the same port number appear in service_conf.py
BASE_IP = os.environ.get("BASE_IP")
BASE_PORT = os.environ.get("BASE_PORT")
IP_PORT = f"{BASE_IP}:{BASE_PORT}"

BASE = f"https://{IP_PORT}"
CONFIG = {
    "entityid": f"http://{IP_PORT}",
    'entity_category': [COC],
    "description": "Test SP",
    "service": {
        "sp": {
            "want_response_signed": True,
            "authn_requests_signed": True,
            "logout_requests_signed": True,
            "endpoints": {
                "assertion_consumer_service": [
                    ("%s/acs/post" % BASE, BINDING_HTTP_POST)
                ],
                "single_logout_service": [
                    ("%s/slo/redirect" % BASE, BINDING_HTTP_REDIRECT),
                    ("%s/slo/post" % BASE, BINDING_HTTP_POST),
                ],
            }
        },
    },
    "key_file": "pki/key.pem",
    "cert_file": "pki/cert.pem",
    "xmlsec_binary": xmlsec_path,
    "metadata": {"local": ["/metadata/idpssodescriptor.xml"]},
    "name_form": NAME_FORMAT_URI,
}
