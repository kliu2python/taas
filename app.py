import os

import eventlet
from eventlet import wsgi
from flask import Flask
from flask_cors import CORS
from flask_restx import Api

from rest import load_api_resource
from utils.logger import get_logger

logger = get_logger()


app = Flask("TAAS")
CORS(app, resources={r"/*": {"origins": "*"}}, methods=['GET', 'HEAD', 'POST', 'OPTIONS'], allow_headers=["Content-Type"])
api = Api(app, version='1.0', title='TaaS API',
          description='TaaS - Test as a Service'
          )
load_api_resource(api)

if __name__ == "__main__":
    enable_debug = os.environ.get("DEBUG", "False") == "True"
    port = int(os.environ.get("LISTEN_PORT", 8000))
    if enable_debug:
        app.run(debug=True, port=port, host="0.0.0.0")
    else:
        wsgi.server(eventlet.listen(("0.0.0.0", port)), app, log=logger)
