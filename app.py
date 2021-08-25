import os

import eventlet
from eventlet import wsgi
from flask import Flask
from flask_restful import Api

from rest import load_api_resource


app = Flask("TAAS")
api = Api(app)
load_api_resource(api)

if __name__ == '__main__':
    enable_debug = os.environ.get("DEBUG", "False") == "True"
    if enable_debug:
        app.run(debug=True, port=8000, host='0.0.0.0')
    else:
        wsgi.server(eventlet.listen(('0.0.0.0', 8000)), app)
