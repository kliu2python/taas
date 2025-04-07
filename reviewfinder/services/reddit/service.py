from datetime import datetime
from typing import Dict, Any, List
import asyncio

from reviewfinder.services.smtp_server import SMTPServer
from reviewfinder.services.reddit.client import RedditClient
from reviewfinder.services.reddit.util import (
    filter_posts_by_topics, format_email_body
)
from utils.logger import get_logger

logger = get_logger(__name__)

MONITORED_TOPICS = ["FortiToken Mobile", "Fortigate", "FAC", "FortiToken Cloud"]


class RedditService:
    """Service for managing Reddit post collection and email notifications."""

    def __init__(self):
        self.smtp_server = SMTPServer.from_config()
        self.reddit_client = None

    async def send_daily_summary(self,
                                 additional_recipients: List[str] = None
                                 ) -> Dict[str, Any]:
        """Send daily summary to subscribers.

        Args:
            additional_recipients: Optional list of additional email addresses

        Returns:
            Dict containing status and details of the operation
        """
        try:
            logger.info("Starting daily summary generation...")
            await self.initialize_reddit_client()

            # Fetch and filter posts
            logger.info("Fetching recent posts...")
            posts = await self.reddit_client.fetch_recent_posts(hours=24)
            logger.info(f"Found {len(posts)} posts in past 24 hours")

            filtered_posts = filter_posts_by_topics(posts, MONITORED_TOPICS)
            filtered_count = sum(
                len(posts) for posts in filtered_posts.values())

            topics_str = ', '.join(MONITORED_TOPICS)
            logger.info(f"Filtered to {filtered_count} posts matching topics: "
                        f"{topics_str}")

            # If no relevant posts, return early
            if filtered_count == 0:
                logger.info("No relevant posts found, skipping email")
                return {
                    "status": "success",
                    "summary_date": datetime.now().isoformat(), "topics": [],
                    "message": "No relevant posts found"}

            # Prepare and send email
            logger.info("Preparing email content...")
            email_body = format_email_body(filtered_posts)
            current_date = datetime.now().strftime('%Y-%m-%d')
            subject = f"Daily Reddit Summary - {current_date}"

            logger.info("Sending email...")
            self.smtp_server.send_email(
                subject=subject, body=email_body,
                recipients=additional_recipients)
            logger.info("Email sent successfully")

            return {
                "status": "success",
                "summary_date": datetime.now().isoformat(),
                "topics": list(filtered_posts.keys()),
                "post_counts": {
                    topic: len(posts) for topic, posts in
                    filtered_posts.items()}
            }

        except Exception as e:
            logger.error(
                f"Error in daily summary task: {str(e)}",
                exc_info=True)
            return {
                "status": "error", "error": str(e),
                "timestamp": datetime.now().isoformat()}
        finally:
            await self.close_reddit_client()

    async def initialize_reddit_client(self):
        """Initialize the Reddit client."""
        if not self.reddit_client:
            logger.info("Initializing Reddit client...")
            self.reddit_client = RedditClient()
            await self.reddit_client.connect()

    async def close_reddit_client(self):
        """Close the Reddit client connection."""
        if self.reddit_client:
            logger.info("Closing Reddit client...")
            await self.reddit_client.close()
            self.reddit_client = None

    @classmethod
    def run_daily_summary(cls):
        """Wrapper method to run the async send_daily_summary.

        Handles the asyncio event loop.
        """
        service = cls()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(service.send_daily_summary())
        finally:
            loop.close()


class AsyncScheduler:
    """Async-compatible scheduler for Reddit service."""

    def __init__(self):
        self.service = RedditService()

    async def run_scheduled_task(self):
        """Run the scheduled task at the specified time."""
        while True:
            now = datetime.now()
            # Schedule for 9:40 AM
            target_time = now.replace(
                hour=9, minute=45, second=0,
                microsecond=0)

            # If we've passed the time today, schedule for tomorrow
            if now > target_time:
                target_time = target_time.replace(day=target_time.day + 1)

            # Calculate seconds until next run
            delay = (target_time - now).total_seconds()

            next_run = target_time.strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"Next summary scheduled for {next_run} "
                        f"({delay / 3600:.2f} hours from now)")
            await asyncio.sleep(delay)

            try:
                result = await self.service.send_daily_summary()
                logger.info(
                    f"Daily summary completed with status: {result['status']}")
            except Exception as e:
                logger.error(
                    f"Error in scheduled task: {str(e)}",
                    exc_info=True)
                # Wait a bit before retrying on error
                await asyncio.sleep(300)


def start_scheduler():
    """Start the scheduler using asyncio event loop."""
    logger.info("Starting Reddit monitoring service...")
    scheduler = AsyncScheduler()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(scheduler.run_scheduled_task())
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}", exc_info=True)
    finally:
        loop.close()
