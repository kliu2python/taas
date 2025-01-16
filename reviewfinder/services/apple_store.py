from app_store_scraper import AppStore


def get_apple_store_reviews(app_name, app_id):
    try:
        app = AppStore(country='us', app_name=app_name, app_id=app_id)
        app.review(how_many=100)
        reviews = []
        for review in app.reviews:
            review["date"] = review["date"].strftime("%Y-%m-%d %H:%M:%S")
            reply = dict()
            if "developerResponse" in review.keys():
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
