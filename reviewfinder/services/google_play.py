import asyncio
from google_play_scraper import reviews_all, Sort


async def get_google_play_reviews(package_name):
    """
    Asynchronously fetch Google Play reviews for a given package name.

    :param package_name: The package name of the app to fetch reviews for.
    :return: A list of formatted review dictionaries.
    """
    # Run the blocking `reviews_all` function in a separate thread
    reviews = await asyncio.to_thread(
        reviews_all,
        app_id=package_name,
        sleep_milliseconds=0,
        sort=Sort.NEWEST
    )

    tmp_list = []
    for review in reviews:
        review["at"] = review["at"].strftime("%Y-%m-%d %H:%M:%S")
        reply = dict()
        if review["replyContent"]:
            reply["replyContent"] = review["replyContent"]
            reply["repliedAt"] = review["repliedAt"]

        if not review["reviewCreatedVersion"]:
            app_version = "unknown"
        else:
            app_version = review["reviewCreatedVersion"]

        tmp = {
            "user": review["userName"],
            "rating": review["score"],
            "reviewCreatedVersion": app_version,
            "review": review["content"],
            "date": review["at"],
            "reply": reply,
            "thumbsUpCount": review["thumbsUpCount"]
        }
        tmp_list.append(tmp)

    return tmp_list


# Example Usage
async def main():
    package_name = "com.example.app"  # Replace with the actual package name
    reviews = await get_google_play_reviews(package_name)
    for review in reviews[:5]:  # Display the first 5 reviews
        print(review)


if __name__ == "__main__":
    asyncio.run(main())