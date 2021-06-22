import cabaltherapi.cards
import io
import requests

from os import environ
from .artist import get_artist_handle
from .twitter import get_recent_tweets_text, update_status, upload_image
from .utils import chunk

# how many of the most recent scryfall spoiler posts to look at
LOOKBACK_COUNT = 160
MODE = environ.get("MODE", "development")
QUERY = "order:spoiled has:imagedata new:art -is:extra -!Plains -!Island -!Swamp -!Mountain -!Forest"


if __name__ == '__main__':
    results = reversed(cabaltherapi.cards.search(QUERY, paginate=False)[:LOOKBACK_COUNT])

    recent_text = get_recent_tweets_text()

    # filter out anything that appears in our most recent timeline
    results = [result for result in results if f"{result['name']}\n" not in recent_text]

    print(f"{len(list(results))} remaining")
    # split it into chunks of four
    results = chunk(results, 4)

    for cardset in results:
        # build the tweet text
        text = ""

        for card in cardset:
            name = card["name"]

            artist = card.get("artist", "Unknown")
            artist = get_artist_handle(artist)

            preview_uri = card.get("preview", {}).get("source_uri")
            preview_uri = f"\n - 🔗: {preview_uri.split('?')[0]}?utm_source=mtgspoilerbot" if preview_uri else None

            scryfall_uri = card.get("scryfall_uri")
            scryfall_uri = f"\n - 🔗: {scryfall_uri.split('?')[0]}?utm_source=mtgspoilerbot"

            uri = preview_uri if preview_uri is not None else scryfall_uri

            text += f"{name}\n - 🎨: {artist}{uri}\n\n"

        text.strip()

        if MODE != "production":
            print(text)
            input("proceed? ")

        # then, upload the images
        media_ids = []

        for card in cardset:
            png_uri = card.get("image_uris", {}).get("png")
            filename = f"{card['id']}.png"

            if png_uri is not None:
                # download the image from scryfall
                png = io.BytesIO(requests.get(png_uri).content)

                # then, upload it to Twitter
                media_ids.append(upload_image(filename, png))


        # now, post it to Twitter
        update_status(text, media_ids)

        # stop at one post unless in production
        if MODE != "production":
            exit()
