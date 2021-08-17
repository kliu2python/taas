import os

from flask import Flask
from flask_restful import Api

from rest import load_api_resource


app = Flask("TAAS")
api = Api(app)
load_api_resource(api)

if __name__ == '__main__':
    enable_debug = os.environ.get("DEBUG", "False") == "True"
    app.run(debug=enable_debug, port=8000, host='0.0.0.0')
