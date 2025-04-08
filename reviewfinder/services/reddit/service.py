import json
from datetime import datetime
import asyncio

from reviewfinder.services.smtp_server import SMTPServer
from reviewfinder.services.reddit.client import RedditClient
from reviewfinder.common.conf import CONF
from reviewfinder.services.reddit.subscription import RedditSubscriptionService
from reviewfinder.services.reddit.util import (
    filter_posts_by_topics,
    format_email_body
)
from utils.logger import get_logger

logger = get_logger()
SCHEDULER = CONF.get("scheduler")
HOUR = SCHEDULER.get("hour", 9)
MINUTE = SCHEDULER.get("minute", 30)
SECOND = SCHEDULER.get("second", 0)
MICROSECOND = SCHEDULER.get("microsecond", 0)


class RedditService:
    """Service for managing Reddit post collection and email notifications."""
    def __init__(self):
        self.smtp_server = SMTPServer.from_config()
        self.reddit_client = None

    async def send_email_to_recipient(
            self, recipient, subject, email_body
    ):
        # Wrap your SMTP call asynchronously if needed
        await self.smtp_server.send_email(subject=subject, body=email_body,
                                          recipients=[recipient])
        return recipient

    async def process_recipient_group(
            self, recipient_group, subject, email_body
    ):
        tasks = [
            self.send_email_to_recipient(recipient, subject, email_body) for
            recipient in recipient_group
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    async def send_daily_summary(self,
                                 additional_recipients: dict = None) -> dict:
        try:
            logger.info("Starting daily summary generation...")
            await self.initialize_reddit_client()

            # Group recipients by their interest topics (
            # assuming additional_recipients is a dict
            # where keys are email addresses and values are interests or topics)
            recipient_groups = {}
            for recipient, interests in additional_recipients.items():
                # Group by topic, assuming each
                # recipient may have one primary interest
                for topic in interests.get("topics"):
                    topic = json.dumps(topic)
                    recipient_groups.setdefault(topic, []).append(recipient)

            logger.info("Fetching recent posts...")
            posts = await self.reddit_client.fetch_recent_posts(hours=24)
            logger.info(f"Found {len(posts)} posts in past 24 hours")

            # Pre-filter posts for each topic
            filtered_posts_by_topic = {
                topic: filter_posts_by_topics(posts, json.loads(topic)) for
                topic in recipient_groups
            }

            # Use one subject and email body per topic group
            tasks = []
            current_date = datetime.now().strftime('%Y-%m-%d')
            for topic, group in recipient_groups.items():
                filtered_posts = filtered_posts_by_topic.get(topic, {})
                filtered_count = sum(
                    len(post_list) for post_list in filtered_posts.values())
                if filtered_count == 0:
                    logger.info(
                        f"No relevant posts for topic {topic}, "
                        f"skipping email for this group")
                    continue

                email_body = format_email_body(filtered_posts)
                subject = f"Daily Reddit Summary - {current_date} - {topic}"
                tasks.append(
                    self.process_recipient_group(group, subject, email_body)
                )

            if not tasks:
                logger.info(
                    "No emails to send, no relevant posts found for topics."
                )
                return {
                    "status": "success",
                    "summary_date": datetime.now().isoformat(),
                    "topics": [],
                    "message": "No relevant posts found"
                }

            # Run all email sending tasks concurrently
            await asyncio.gather(*tasks)
            logger.info("Emails sent successfully")
            return {
                "status": "success",
                "summary_date": datetime.now().isoformat(),
                "topics": list(filtered_posts_by_topic.keys())
            }

        except Exception as e:
            logger.error(f"Error in daily summary task: {str(e)}",
                         exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
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
            # Schedule for 9:30 AM
            target_time = now.replace(
                hour=HOUR, minute=MINUTE, second=SECOND,
                microsecond=MICROSECOND)

            subscriptions = RedditSubscriptionService().get_all_subscriptions()

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
                result = await self.service.send_daily_summary(
                    subscriptions.get("subscriptions")
                )
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
