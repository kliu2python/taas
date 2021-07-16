import json

from flask import jsonify
from flask_restful import Resource, request

from rest import RestApi
from model.manager import ModelManager, ModelType


rest = RestApi(base_route="/")
ModelManager()


@rest.route("imageclassifier")
class ImageClassifier(Resource):
    """
    post data type:
    {
        "inputs": [
            "base64_image1",
            "base64_image2"
        ]
    }
    """
    def post(self):
        data = json.loads(request.json)
        results = ModelManager().inference(ModelType.IMAGECLASSIFIER, **data)
        return jsonify({"results": results})
