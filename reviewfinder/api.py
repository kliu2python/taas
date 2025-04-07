from flask_restx import Resource, reqparse
import asyncio
from datetime import datetime
from flask import jsonify, request, abort

from rest import RestApi
from reviewfinder.services.apple_store import get_apple_store_reviews
from reviewfinder.services.google_play import get_google_play_reviews
from reviewfinder.services.reddit import (
    RedditService,
    RedditSubscriptionService,
    RedditClient,
    filter_posts_by_topics,

)

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


@rest.route("reddit/posts")
class RedditPosts(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            'hours',
            type=int,
            default=24,
            help='Hours to look back'
        )
        self.parser.add_argument(
            'topics',
            type=str,
            action='append',
            help='Topics to filter by (can be specified multiple times)'
        )

    def get(self):
        """Get Reddit posts with optional filtering by time and topics"""
        args = self.parser.parse_args()
        hours = args.get('hours', 24)
        topics = args.get('topics', [])

        async def fetch_posts():
            client = RedditClient()
            try:
                posts = await client.fetch_recent_posts(hours=hours)
                if topics:
                    filtered_posts = filter_posts_by_topics(posts, topics)
                    return {"platform": "Reddit", "topics": filtered_posts}
                return {"platform": "Reddit", "posts": posts}
            finally:
                await client.close()

        return asyncio.run(fetch_posts())


@rest.route("reddit/summary")
class RedditSummary(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            'send_email',
            type=bool,
            default=False,
            help='Whether to send email summary'
        )

    def get(self):
        """Generate a summary of Reddit posts and optionally send email"""
        args = self.parser.parse_args()
        send_email = args.get('send_email', False)

        async def generate_summary():
            client = RedditClient()
            try:
                posts = await client.fetch_recent_posts(hours=24)
                topics = ["FortiToken Mobile",
                          "Fortigate",
                          "FAC",
                          "FortiToken Cloud"
                          ]
                filtered_posts = filter_posts_by_topics(posts, topics)
                
                if send_email:
                    await RedditService().send_daily_summary()
                
                return {
                    "platform": "Reddit",
                    "generated_at": datetime.now().isoformat(),
                    "summary": filtered_posts
                }
            finally:
                await client.close()

        return asyncio.run(generate_summary())


@rest.route("reddit/schedule")
class RedditSchedule(Resource):
    def post(self):
        """Trigger an immediate run of the scheduled task"""
        RedditService().send_daily_summary()
        return {"message": "Manual run triggered successfully"}


@rest.route("subscriptions")
class SubscriptionManagement(Resource):
    def post(self):
        """Subscribe a user to a topic"""
        data = request.get_json()
        if not data or 'email' not in data or 'topic' not in data:
            abort(400, description="Missing email or topic in request body")

        result = RedditSubscriptionService.subscribe(data['email'], data['topic'])
        if result['status'] == 'error':
            abort(500, description=result['message'])
        return jsonify(result)

    def delete(self):
        """Unsubscribe a user from a topic"""
        data = request.get_json()
        if not data or 'email' not in data or 'topic' not in data:
            abort(400, description="Missing email or topic in request body")

        result = RedditSubscriptionService.unsubscribe(data['email'], data['topic'])
        if result['status'] == 'error':
            return jsonify(result), 404
        return jsonify(result)

    def get(self):
        """Get subscriptions, optionally filtered by email"""
        email = request.args.get('email')

        if email:
            # Get subscriptions for specific email
            result = RedditSubscriptionService.get_user_subscriptions(email)
        else:
            # Get all subscriptions
            result = RedditSubscriptionService.get_all_subscriptions()

        if result['status'] == 'error':
            abort(500, description=result['message'])
        return jsonify(result)


@rest.route("topics")
class TopicManagement(Resource):
    def get(self):
        """Get all available topics"""
        result = RedditSubscriptionService.get_all_topics()
        if result['status'] == 'error':
            abort(500, description=result['message'])
        return jsonify(result)

    def post(self):
        """Add a new topic"""
        data = request.get_json()
        if not data or 'name' not in data:
            abort(400, description="Missing topic name in request body")

        result = RedditSubscriptionService.add_topic(data['name'])
        if result['status'] == 'error':
            abort(500, description=result['message'])
        return jsonify(result)


@rest.route("reddit/summary")
class RedditSummary(Resource):
    def post(self):
        """Manually trigger the Reddit summary generation and email sending"""
        reddit_service = RedditService()
        result = asyncio.run(reddit_service.send_daily_summary())
        if result['status'] == 'error':
            abort(500, description=result['error'])
        return jsonify(result)
