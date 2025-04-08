import asyncpraw
from datetime import datetime, timedelta
import pytz

from reviewfinder.common.conf import CONF
from utils.logger import get_logger

logger = get_logger()

REDDIT_CONF = CONF.get("reddit")


class RedditClient:
    """Client for interacting with Reddit API."""

    def __init__(self):
        self.reddit = None

    async def connect(self):
        """Initialize and connect to Reddit API."""
        self.reddit = asyncpraw.Reddit(
            client_id=REDDIT_CONF.get("client_id"),
            client_secret=REDDIT_CONF.get("client_secret"),
            user_agent=REDDIT_CONF.get("user_agent")
        )
        logger.info("setup the reddit client successfully..")

    async def close(self):
        """Close the Reddit client connection."""
        if self.reddit:
            await self.reddit.close()
            logger.info("close the reddit client successfully..")

    async def fetch_recent_posts(self, hours: int = 24) -> list:
        """
        Fetch posts from the last specified hours.

        Args:
            hours: Number of hours to look back for posts

        Returns:
            List of posts with their details and comments
        """
        if not self.reddit:
            await self.connect()

        subreddit = await self.reddit.subreddit(
            REDDIT_CONF.get("subreddit_name")
        )
        posts_list = []
        cutoff_time = datetime.now(pytz.UTC) - timedelta(hours=hours)

        async for post in subreddit.new(limit=None):
            post_time = datetime.fromtimestamp(post.created_utc, pytz.UTC)
            if post_time < cutoff_time:
                break

            await post.load()
            await post.comments.replace_more(limit=0)

            answers = []
            for comment in post.comments:
                author = comment.author.name if comment.author else "[deleted]"
                answer_obj = {
                    "author": author,
                    "body": comment.body,
                    "replies": await self.get_comment_replies(comment)
                }
                answers.append(answer_obj)

            update_time = self._get_update_time(post)
            post_data = self._create_post_data(
                post, answers, post_time, update_time
            )
            posts_list.append(post_data)

        logger.info(f"fetched {len(posts_list)} post in the past {hours} hours")
        return posts_list

    async def get_comment_replies(self, comment) -> list:
        """
        Recursively retrieve replies for a comment.

        Args:
            comment: Reddit comment object

        Returns:
            List of reply dictionaries with author and content
        """
        replies_data = []
        for reply in comment.replies:
            reply_data = {
                "author": reply.author.name if reply.author else "[deleted]",
                "body": reply.body,
                "replies": await self.get_comment_replies(reply)
            }
            replies_data.append(reply_data)
        return replies_data

    def _get_update_time(self, post) -> str:
        """Get the formatted update time for a post."""
        if isinstance(post.edited, (int, float)):
            timestamp = post.edited
        else:
            timestamp = post.created_utc
        return datetime.fromtimestamp(timestamp, pytz.UTC).isoformat()

    def _create_post_data(
        self,
        post,
        answers: list,
        post_time: datetime,
        update_time: str
    ) -> dict:
        """Create a formatted dictionary of post data."""
        return {
            "author": post.author.name if post.author else "[deleted]",
            "title": post.title,
            "body": post.selftext,
            "url": post.url,
            "answers": answers,
            "post_time": post_time.isoformat(),
            "update_time": update_time
        }
