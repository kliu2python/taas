import asyncio
from app_store_scraper import AppStore


async def get_apple_store_reviews(app_name, app_id):
    """
    Asynchronously fetch Apple Store reviews for a given app.

    :param app_name: The name of the app.
    :param app_id: The Apple Store app ID.
    :return: A list of formatted review dictionaries or an error message.
    """
    try:
        # Run the blocking AppStore initialization
        # and review fetching in a background thread
        app = await asyncio.to_thread(
            AppStore, country='us', app_name=app_name, app_id=app_id
        )
        await asyncio.to_thread(app.review, how_many=100)

        reviews = []
        for review in app.reviews:
            review["date"] = review["date"].strftime("%Y-%m-%d %H:%M:%S")
            reply = {}
            if "developerResponse" in review:
                reply["replyContent"] = review["developerResponse"]["body"]
                reply["repliedAt"] = review["developerResponse"]["modified"]
            reviews.append({
                'user': review['userName'],
                'rating': review['rating'],
                'review': review['review'],
                'date': review['date'],
                'reply': reply
            })
        return reviews
    except Exception as e:
        return {"error": str(e)}


# Example Usage
async def main():
    app_name = "example-app"  # Replace with the actual app name
    app_id = "1234567890"  # Replace with the actual app ID
    reviews = await get_apple_store_reviews(app_name, app_id)
    if "error" in reviews:
        print(f"Error: {reviews['error']}")
    else:
        print("Fetched reviews:")
        for review in reviews[:5]:  # Display the first 5 reviews
            print(review)


if __name__ == "__main__":
    asyncio.run(main())
