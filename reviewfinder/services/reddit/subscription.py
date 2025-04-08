import json
import requests
from datetime import datetime
import pytz
from typing import Dict, Any, List

from utils.logger import get_logger

logger = get_logger()

MONGODB_API_BASE = "http://10.160.24.88:31742/api/v1/mongodb"
DB_NAME = "reviewfinder"


class RedditSubscriptionService:
    """Service for managing Reddit topic subscriptions."""

    @staticmethod
    def subscribe(email: str, topic: list) -> Dict[str, Any]:
        """
        Subscribe a user to a topic.

        Args:
            email: User's email address
            topic: List of topics name to subscribe to

        Returns:
            Dict with operation status and message
        """
        try:
            # Ensure user exists
            user_data = {"email": email}

            # Create subscription
            subscription_data = {
                "email": email,
                "topic": topic
            }
            start_time = datetime.now()
            if RedditSubscriptionService._find_documents(
                    "subscriptions",
                    user_data):
                logger.info(f"complete find_documents {datetime.now() - start_time}")
                start_time = datetime.now()
                if RedditSubscriptionService._find_documents(
                        "subscriptions", subscription_data):
                    sub_response = True
                    logger.info(
                        f"complete find_document {datetime.now() - start_time}")
                else:
                    subscription_data["updated_at"] = datetime.now(
                        pytz.UTC
                    ).isoformat()
                    subscription_tmp_data = {"filter": user_data,
                                             "update": subscription_data}
                    start_time = datetime.now()
                    sub_response = RedditSubscriptionService._update_document(
                        "subscriptions", subscription_tmp_data
                    )
                    logger.info(
                        f"complete update_document"
                        f" {datetime.now() - start_time}")
            else:
                subscription_data["created_at"] = datetime.now(
                    pytz.UTC
                ).isoformat()
                sub_response = RedditSubscriptionService._create_document(
                    "subscriptions", subscription_data)
            if not sub_response:
                raise Exception("Failed to create subscription")

            return {
                "status": "success",
                "message": "Subscription created successfully"
            }

        except Exception as e:
            logger.error(f"Subscription error: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def unsubscribe(email: str, topic: str) -> Dict[str, Any]:
        """
        Unsubscribe a user from a topic.

        Args:
            email: User's email address
            topic: Topic to unsubscribe from

        Returns:
            Dict with operation status and message
        """
        try:
            filter_query = {
                "filter": {
                    "email": email,
                    "topic": topic
                }
            }

            response = requests.delete(
                f"{MONGODB_API_BASE}/document/delete",
                params={"db": DB_NAME, "collection": "subscriptions"},
                json=filter_query
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('deleted_count', 0) > 0:
                    return {
                        "status": "success",
                        "message": "Subscription deleted successfully"
                    }

            return {"status": "error", "message": "Subscription not found"}

        except Exception as e:
            logger.error(f"Unsubscribe error: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def _create_document(collection: str, data: dict) -> bool:
        """Create a document in the specified collection."""
        response = requests.post(
            f"{MONGODB_API_BASE}/document/insert",
            params={"db": DB_NAME, "collection": collection},
            json=data
        )
        return response.status_code == 200

    @staticmethod
    def _update_document(collection: str, data: dict) -> bool:
        """Create a document in the specified collection."""
        response = requests.put(
            f"{MONGODB_API_BASE}/document/update",
            params={"db": DB_NAME, "collection": collection},
            json=data
        )
        return response.status_code == 200

    @staticmethod
    def _find_documents(
        collection: str,
        filter_query: dict
    ) -> List[Dict[str, Any]]:
        """Find documents in the specified collection."""
        response = requests.get(
            f"{MONGODB_API_BASE}/document/find",
            params={
                "db": DB_NAME,
                "collection": collection,
                "filter": json.dumps(filter_query)
            }
        )
        if response.status_code != 200:
            return []
        return response.json()

    @staticmethod
    def get_user_subscriptions(email: str) -> Dict[str, Any]:
        """
        Get all subscriptions for a user

        Args:
            email: User's email address

        Returns:
            Dict containing user's subscribed topics
        """
        try:
            filter_query = {"email": email}
            params = {
                    "db": DB_NAME, "collection": "subscriptions",
                    "filter": filter_query
                }
            response = requests.get(
                f"{MONGODB_API_BASE}/document/find",
                params=params
            )

            if response.status_code != 200:
                raise Exception("Failed to fetch subscriptions")

            subscriptions = response.json().get('documents', [])
            topics = [sub['topic'] for sub in subscriptions]

            return {"status": "success", "email": email, "topics": topics}

        except Exception as e:
            logger.error(f"Error fetching subscriptions: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_all_subscriptions() -> Dict[str, Any]:
        """Get all subscriptions grouped by email and topic.

        Returns:
            Dict containing all subscriptions organized by email
        """
        try:
            response = requests.get(
                f"{MONGODB_API_BASE}/document/find",
                params={
                    "db": DB_NAME, "collection": "subscriptions",
                    "filter": "{}"
                }
            )

            if response.status_code != 200:
                raise Exception("Failed to fetch subscriptions")

            subscriptions = response.json()

            # Organize subscriptions by email
            organized_subs = {}
            for sub in subscriptions:
                email = sub.get('email')
                topic = sub.get('topic')
                created_at = sub.get('created_at')

                if email not in organized_subs:
                    organized_subs[email] = {
                        'topics': [],
                        'subscription_count': 0,
                        'subscriptions': []
                    }

                organized_subs[email]['topics'].append(topic)
                organized_subs[email]['subscription_count'] += 1
                organized_subs[email]['subscriptions'].append(
                    {'topic': topic, 'created_at': created_at})

            return {
                "status": "success",
                "total_subscriptions": len(subscriptions),
                "total_subscribers": len(organized_subs),
                "subscriptions": organized_subs
            }

        except Exception as e:
            logger.error(f"Error fetching all subscriptions: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_all_topics() -> Dict[str, Any]:
        """
        Get all available topics

        Returns:
            Dict containing all topics
        """
        try:
            response = requests.get(
                f"{MONGODB_API_BASE}/document/find",
                params={"db": DB_NAME, "collection": "topics", "filter": "{}"}
            )

            if response.status_code != 200:
                raise Exception("Failed to fetch topics")

            topics = response.json().get('documents', [])
            return {
                "status": "success",
                "topics": [topic['name'] for topic in topics]
            }

        except Exception as e:
            logger.error(f"Error fetching topics: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def add_topic(topic_name: str) -> Dict[str, Any]:
        """
        Add a new topic

        Args:
            topic_name: Name of the topic to add

        Returns:
            Dict with operation status
        """
        try:
            topic_data = {
                "name": topic_name,
                "created_at": datetime.now(pytz.UTC).isoformat()
            }

            response = requests.post(
                f"{MONGODB_API_BASE}/document/insert",
                params={"db": DB_NAME, "collection": "topics"},
                json=topic_data)

            if response.status_code != 200:
                raise Exception("Failed to create topic")

            return {"status": "success", "message": "Topic added successfully"}

        except Exception as e:
            logger.error(f"Error adding topic: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_subscribers_for_topic(topic_name: str) -> List[str]:
        """
        Get all subscribers for a specific topic

        Args:
            topic_name: Name of the topic

        Returns:
            List of subscriber email addresses
        """
        try:
            filter_query = {"topic": topic_name}
            response = requests.get(
                f"{MONGODB_API_BASE}/document/find",
                params={
                    "db": DB_NAME, "collection": "subscriptions",
                    "filter": json.dumps(filter_query)
                }
            )

            if response.status_code != 200:
                return []

            subscriptions = response.json().get('documents', [])
            return [sub['email'] for sub in subscriptions]

        except Exception as e:
            logger.error(f"Error fetching subscribers: {str(e)}")
            return []
