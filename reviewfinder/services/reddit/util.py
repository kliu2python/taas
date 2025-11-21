import json

import requests


def filter_posts_by_topics(posts: list, topics: list) -> dict:
    """
    Filter posts by multiple topics and return a dictionary of results
    organized by topic
    """
    results = {topic: [] for topic in topics}

    for post in posts:
        title = post.get("title", "").lower()
        body = post.get("body", "").lower()

        for topic in topics:
            if topic.lower() in title or topic.lower() in body:
                results[topic].append(post)

    return results


def get_subscribers_for_topic(topic_name: str) -> list:
    """Get all subscribers for a specific topic"""
    filter_query = {"topic": topic_name}
    response = requests.get(
        "http://localhost:5000/api/v1/mongodb/document/find",
        params={
            "db": "reviewfinder", "collection": "subscriptions",
            "filter": json.dumps(filter_query)
        }
    )
    if response.status_code != 200:
        return []

    subscriptions = response.json().get('documents', [])
    return [sub['email'] for sub in subscriptions]


def format_email_body(filtered_posts: dict) -> str:
    """Format the email body with posts organized by topic"""
    email_body = "Daily Reddit Post Summary\n"
    email_body += "=" * 50 + "\n\n"

    for topic, posts in filtered_posts.items():
        if posts:
            email_body += f"Topic: {topic}\n"
            email_body += "-" * 30 + "\n"

            for idx, post in enumerate(posts, start=1):
                email_body += f"Post {idx}:\n"
                email_body += f"Title: {post['title']}\n"
                email_body += f"Author: {post['author']}\n"
                email_body += f"URL: {post['url']}\n"
                email_body += f"Posted: {post['post_time']}\n"
                email_body += f"Content:\n{post['body']}\n"

                if post['answers']:
                    email_body += "\nTop Comments:\n"
                    for answer in post['answers'][:3]:
                        email_body += (f"- {answer['author']}:"
                                       f" {answer['body'][:200]}...\n")

                email_body += "\n" + "-" * 20 + "\n"

            email_body += "\n"

    return email_body
