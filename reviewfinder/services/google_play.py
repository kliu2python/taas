from google_play_scraper import reviews_all, Sort


def get_google_play_reviews(package_name):
    reviews = reviews_all(
        app_id=package_name, sleep_milliseconds=0, sort=Sort.NEWEST
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
