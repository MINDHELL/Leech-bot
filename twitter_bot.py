import asyncio
import os
import time
import requests
from pyrogram import Client
from pyrogram.types import InputMediaVideo, InputMediaPhoto
from health_check import start_health_check

# === CONFIG ===
API_ID = int(os.environ.get("API_ID", 27788368))
API_HASH = os.environ.get("API_HASH", "9df7e9ef3d7e4145270045e5e43e1081")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7769792227:AAHTVq8KCOHYg9oZOBvGszU3bms7BsH94k0")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", -1002682688904))

# Add your tweet links here
TWEET_LINKS = [
    "https://twitter.com/HoodiiiDurant/status/1942522168732180806"
]

# === Initialize Pyrogram Bot ===
app = Client("twitter_dl_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# === Extract media & caption using vxtwitter API ===
def extract_from_vxtwitter(tweet_url):
    try:
        tweet_id = tweet_url.split("/status/")[1].split("?")[0]
        api_url = f"https://api.vxtwitter.com/Twitter/status/{tweet_id}"

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(api_url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"❌ API error {response.status_code} for: {tweet_url}")
            return None, None

        data = response.json()
        caption = data.get("text", "")
        media_urls = []

        for item in data.get("media", []):
            mtype = item.get("type")
            url = item.get("url")
            if mtype == "photo":
                media_urls.append(("photo", url))
            elif mtype == "video":
                media_urls.append(("video", url))

        return caption, media_urls
    except Exception as e:
        print("❌ Exception while fetching media:", e)
        return None, None

# === Bot Logic ===
async def main():
    await app.start()
    print("🤖 Bot started... Monitoring tweet links")

    while True:
        for tweet in TWEET_LINKS:
            caption, media = extract_from_vxtwitter(tweet)

            if not media:
                print(f"⚠️ No media found for: {tweet}")
                continue

            try:
                group = []
                for i, (mtype, url) in enumerate(media):
                    if mtype == "photo":
                        group.append(InputMediaPhoto(media=url, caption=caption if i == 0 else None))
                    elif mtype == "video":
                        group.append(InputMediaVideo(media=url, caption=caption if i == 0 else None))

                if len(group) == 1:
                    if group[0].media.endswith(".mp4"):
                        await app.send_video(CHANNEL_ID, group[0].media, caption=f"{caption}\n🔗 {tweet}")
                    else:
                        await app.send_photo(CHANNEL_ID, group[0].media, caption=f"{caption}\n🔗 {tweet}")
                else:
                    await app.send_media_group(CHANNEL_ID, group)

                print(f"✅ Sent: {tweet}")
            except Exception as e:
                print(f"❌ Telegram error: {e}")

        print("🕒 Sleeping 30 minutes before checking again...")
        await asyncio.sleep(1800)  # 30 minutes

# === Run the bot ===
if __name__ == "__main__":
    start_health_check()
    asyncio.run(main())
