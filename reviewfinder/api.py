from flask_restx import Resource
import asyncio

from rest import RestApi
from reviewfinder.services.apple_store import get_apple_store_reviews
from reviewfinder.services.google_play import get_google_play_reviews

rest = RestApi(base_route="/reviewfinder/v1/")


@rest.route("google_play/<string:package_name>")
class GooglePlayReview(Resource):
    def get(self, package_name: str):
        reviews = asyncio.run(get_google_play_reviews(package_name))
        return {"platform": "Google Play", "reviews": reviews}


@rest.route("apple_store/<string:app_name>/<string:app_id>")
class AppleStoreReview(Resource):
    def get(self, app_name: str, app_id: str):
        reviews = asyncio.run(get_apple_store_reviews(app_name, app_id))
        return {"platform": "App Store", "reviews": reviews}
