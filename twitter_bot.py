import os
import requests
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo
from health_check import start_health_check

# === Config ===
API_ID = int(os.environ.get("API_ID", 27788368))
API_HASH = os.environ.get("API_HASH", "9df7e9ef3d7e4145270045e5e43e1081")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7769792227:AAHTVq8KCOHYg9oZOBvGszU3bms7BsH94k0")
ADMIN_ID = 6860316927  # Your Telegram user ID

# === Init ===
app = Client("twitter_dl_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# === Tweet media extractor ===
def extract_from_vxtwitter(tweet_url):
    try:
        tweet_id = tweet_url.split("/status/")[1].split("?")[0]
        api_url = f"https://api.vxtwitter.com/Twitter/status/{tweet_id}"
        r = requests.get(api_url, timeout=10)
        if r.status_code != 200:
            print(f"❌ API error {r.status_code}")
            return None, None
        data = r.json()
        caption = data.get("text", "")
        media = []
        for m in data.get("media", []):
            if m["type"] == "photo":
                media.append(("photo", m["url"]))
            elif m["type"] == "video":
                media.append(("video", m["url"]))
        return caption, media
    except Exception as e:
        print("❌ Media extraction error:", e)
        return None, None

# === /start command ===
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    await message.reply_text("👋 Hi! I'm ready.\nSend a tweet link or use /get <tweet_url> to download media.")

# === /get <link> command ===
@app.on_message(filters.command("get") & filters.private)
async def get_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("❗ Please use: /get <tweet_url>")

    tweet_url = message.command[1]
    caption, media = extract_from_vxtwitter(tweet_url)

    if not media:
        return await message.reply("⚠️ No media found in the tweet.")

    group = []
    for i, (mtype, url) in enumerate(media):
        if mtype == "photo":
            group.append(InputMediaPhoto(media=url, caption=caption if i == 0 else None))
        elif mtype == "video":
            group.append(InputMediaVideo(media=url, caption=caption if i == 0 else None))

    try:
        if len(group) == 1:
            if group[0].media.endswith(".mp4"):
                await message.reply_video(group[0].media, caption=caption)
            else:
                await message.reply_photo(group[0].media, caption=caption)
        else:
            await message.reply_media_group(group)
    except Exception as e:
        await message.reply(f"❌ Telegram error:\n`{e}`")

# === Detect raw tweet links ===
@app.on_message(filters.private & filters.text)
async def auto_link_parser(client: Client, message: Message):
    if "twitter.com" in message.text or "x.com" in message.text:
        message.text = f"/get {message.text}"
        await get_cmd(client, message)

# === Main bot runner ===
async def main():
    await app.start()
    print("🤖 Bot started")
    try:
        await app.send_message(ADMIN_ID, "✅ Bot is now online!")
    except:
        print("❗ Could not send startup message.")
    await idle()

if __name__ == "__main__":
    start_health_check()
    asyncio.run(main())
