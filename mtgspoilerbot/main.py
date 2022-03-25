import cabaltherapi.cards
import io
import requests

from os import environ
from .artist import get_artist_handle
from .twitter import get_recent_tweets_text, update_status, upload_image

# how many of the most recent scryfall spoiler posts to look at
LOOKBACK_COUNT = 16
MODE = environ.get("MODE", "development")
QUERY = "order:spoiled has:imagedata -is:extra -!Plains -!Island -!Swamp -!Mountain -!Forest"


if __name__ == '__main__':
    results = reversed(cabaltherapi.cards.search(QUERY, paginate=False)[:LOOKBACK_COUNT])

    recent_text = get_recent_tweets_text()

    # filter out anything that appears in our most recent timeline
    results = [result for result in results if result['name'].split(" // ")[0].replace('"', "") not in recent_text.replace("&amp;", "&")]

    # for each card, if it has a quotation mark in the name, mark it as non-English
    for result in results:
        if '"' in result["name"]:
            result["lang"] = "funny"

    print(f"{len(list(results))} remaining")

    # split it into chunks of four
    while results:
        # each non-English name reduces the number of cards we can post by one, minimum of two
        num_non_english = sum([True if card["lang"] != "en" else False for card in results[0:4]])
        num_cards = max(4 - num_non_english, 3)

        cardset = results[0:num_cards]
        del results[0:num_cards]

        # build the tweet text
        text = ""

        for card in cardset:
            name = card["name"]

            artist = card.get("artist", "Unknown")
            artist = get_artist_handle(artist)

            preview_uri = card.get("preview", {}).get("source_uri")
            preview_uri = f"\n🔗: {preview_uri}" if preview_uri else None

            scryfall_uri = card.get("scryfall_uri")
            scryfall_uri = f"\n{'💫' if preview_uri else '🔗'}: {scryfall_uri.split('?')[0]}?utm_source=mtgspoilerbot"

            if preview_uri and card["lang"] != "en":
                uri = preview_uri + scryfall_uri
            elif preview_uri:
                uri = preview_uri
            else:
                uri = scryfall_uri

            # text += f"{name}\n - 🎨: {artist}{uri}\n\n"
            text += f"{name} (🎨: {artist}){uri}\n\n"

        text = text.strip()

        # when run manually
        if MODE != "production":
            print(text)

            answer = input("Proceed? ")
            if not answer or answer[0].lower() != "y":
                exit()

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


        # now, post it to Twitter, making it shorter if necessary
        try:
            update_status(text, media_ids)
        except:
            text = text.split('\n\n')
            text.pop()
            text = '\n\n'.join(text)

            media_ids.pop()

            update_status(text, media_ids)

        # stop at one post, since prod now runs every 15 minutes
        exit()
