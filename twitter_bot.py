import threading
from health_check import start_health_check
import asyncio
import requests
from pyrogram import Client
from pyrogram.types import InputMediaVideo, InputMediaPhoto
import os

# === CONFIG (from Koyeb env vars or fallback) ===
API_ID = int(os.environ.get("API_ID", 27788368))
API_HASH = os.environ.get("API_HASH", "9df7e9ef3d7e4145270045e5e43e1081")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7769792227:AAHTVq8KCOHYg9oZOBvGszU3bms7BsH94k0")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", -1002682688904))

# Add tweet links here
TWEET_LINKS = [
    "https://twitter.com/HoodiiiDurant/status/1942522168732180806"
]

app = Client("twitter_dl_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Extract media and caption from vxtwitter.com
def extract_from_vxtwitter(tweet_url):
    try:
        cleaned = tweet_url.split("?")[0]
        tweet_id = cleaned.split("/status/")[1]
        vx_url = f"https://vxtwitter.com/HoodiiiDurant/status/{tweet_id}"

        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(vx_url, headers=headers, timeout=15)
        html = res.text

        # Caption
        desc_tag = '<meta name="description" content="'
        start = html.find(desc_tag)
        if start == -1:
            return None, None
        desc = html[start + len(desc_tag):].split('"')[0]

        # Media
        media_urls = []
        for line in html.splitlines():
            if "video.twimg.com" in line and ".mp4" in line:
                media = line.split('"')[1]
                media_urls.append(("video", media))
            elif "pbs.twimg.com/media/" in line and (".jpg" in line or ".png" in line):
                media = line.split('"')[1]
                media_urls.append(("photo", media))

        return desc, media_urls
    except Exception as e:
        print("❌ Extraction failed:", e)
        return None, None

async def main():
    await app.start()
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

            

# 🔰 Run the Bot
if __name__ == "__main__":
    start_health_check()
    asyncio.run(main())
