"""
Reddit service module for handling Reddit-related functionality.
This module serves as the main entry point for Reddit services.
"""

from reviewfinder.services.reddit import (
    RedditClient,
    RedditService,
    RedditSubscriptionService,
    filter_posts_by_topics,
    format_email_body,
    get_subscribers_for_topic,
    start_scheduler
)

__all__ = [
    'RedditClient',
    'RedditService',
    'RedditSubscriptionService',
    'filter_posts_by_topics',
    'format_email_body',
    'get_subscribers_for_topic',
    'start_scheduler'
]

if __name__ == "__main__":
    from utils.logger import get_logger
    logger = get_logger()
    logger.info("Starting Reddit monitoring service")
    start_scheduler()
