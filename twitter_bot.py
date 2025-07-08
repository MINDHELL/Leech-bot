import threading
from health_check import start_health_check
import asyncio
import requests
from pyrogram import Client

# ==== CONFIG ====
API_ID = 27788368
API_HASH = "9df7e9ef3d7e4145270045e5e43e1081"
BOT_TOKEN = "7769792227:AAHTVq8KCOHYg9oZOBvGszU3bms7BsH94k0"
CHANNEL_ID = -1002682688904

TWEET_LINKS = [
    "https://twitter.com/HoodiiiDurant/status/1942522168732180806"
]
# ================

app = Client("x2twitter_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def get_download_link(tweet_url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
        }
        data = {
            "url": tweet_url
        }

        r = requests.post("https://x2download.app/api/ajaxSearch", data=data, headers=headers)
        if r.status_code != 200 or 'result' not in r.text:
            return None, None

        # Manually extract download URL from response
        res_text = r.text
        start = res_text.find("https://")  # crude but works
        end = res_text.find(".mp4", start)
        video_url = res_text[start:end+4]

        title_start = res_text.find('"title":"') + 9
        title_end = res_text.find('"', title_start)
        title = res_text[title_start:title_end]

        return title, video_url
    except Exception as e:
        print(f"❌ Error parsing x2download: {e}")
        return None, None

async def main():
    await app.start()

    for tweet in TWEET_LINKS:
        title, media_url = get_download_link(tweet)
        if not media_url:
            print(f"⚠️ No media found for: {tweet}")
            continue
        try:
            await app.send_video(CHANNEL_ID, media=media_url, caption=f"{title}\n🔗 {tweet}")
            print(f"✅ Sent: {tweet}")
        except Exception as e:
            print(f"❌ Telegram error: {e}")
            

# 🔰 Run the Bot
if __name__ == "__main__":
    threading.Thread(target=start_health_check, daemon=True).start()
    bot.run()
