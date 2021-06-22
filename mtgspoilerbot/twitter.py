import tweepy

from os import environ


CONSUMER_KEY = environ.get("CONSUMER_KEY")
CONSUMER_SECRET_KEY = environ.get("CONSUMER_SECRET_KEY")
ACCESS_KEY = environ.get("ACCESS_KEY")
ACCESS_SECRET_KEY = environ.get("ACCESS_SECRET_KEY")


# Authenticate to Twitter
__auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET_KEY)
__auth.set_access_token(ACCESS_KEY, ACCESS_SECRET_KEY)

# Create API object
__API = tweepy.API(__auth)


def print_list_members(list_id):
    list_members = __API.list_members(list_id=list_id, tweet_mode="extended", count=260)

    for member in list_members:
        print(f'  "{member.name}": "{member.screen_name}",')

def get_recent_tweets_text() -> str:
    timeline = __API.user_timeline(count=80, tweet_mode="extended")

    return "\n".join([tweet.full_text for tweet in timeline])

def upload_image(filename, image) -> int:
    media = __API.media_upload(filename, file=image)

    return media.media_id

def update_status(text, media_ids):
    foo = __API.update_status(text,
                              media_ids=media_ids,
                              auto_populate_reply_metadata=False,
                              card_uri="tombstone://card",
                              tweet_mode="extended")

    return foo