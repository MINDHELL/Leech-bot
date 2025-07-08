import os
import requests
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo
from health_check import start_health_check

# ==== CONFIG ====
API_ID = int(os.environ.get("API_ID", 27788368))
API_HASH = os.environ.get("API_HASH", "9df7e9ef3d7e4145270045e5e43e1081")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7769792227:AAHTVq8KCOHYg9oZOBvGszU3bms7BsH94k0")
ADMIN_ID = 6860316927  # Your personal Telegram user ID

# ==== INIT ====
app = Client("twitter_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ==== Extract media from vxtwitter API ====
def extract_from_vxtwitter(tweet_url):
    try:
        tweet_id = tweet_url.split("/status/")[1].split("?")[0]
        api_url = f"https://api.vxtwitter.com/Twitter/status/{tweet_id}"
        response = requests.get(api_url, timeout=10)

        if response.status_code != 200:
            print(f"❌ API error {response.status_code}")
            return None, None

        data = response.json()
        caption = data.get("text", "")
        media_list = []

        for item in data.get("media", []):
            mtype = item.get("type")
            url = item.get("url")
            if mtype == "photo":
                media_list.append(("photo", url))
            elif mtype == "video":
                media_list.append(("video", url))

        return caption, media_list
    except Exception as e:
        print("❌ Extraction failed:", e)
        return None, None

# ==== /start ====
@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    print("📥 /start received")
    await message.reply(
        "👋 I'm alive!\n\n"
        "Send a Twitter/X link directly or use:\n"
        "`/get https://twitter.com/...`",
        quote=True
    )

# ==== /get ====
@app.on_message(filters.command("get") & filters.private)
async def get_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("⚠️ Please send a valid tweet link.\nExample:\n`/get https://twitter.com/...`")

    tweet_url = message.command[1]
    caption, media = extract_from_vxtwitter(tweet_url)

    if not media:
        return await message.reply("❌ No media found for this tweet.")

    try:
        group = []
        for i, (mtype, url) in enumerate(media):
            if mtype == "photo":
                group.append(InputMediaPhoto(media=url, caption=caption if i == 0 else None))
            elif mtype == "video":
                group.append(InputMediaVideo(media=url, caption=caption if i == 0 else None))

        if len(group) == 1:
            if group[0].media.endswith(".mp4"):
                await message.reply_video(group[0].media, caption=caption)
            else:
                await message.reply_photo(group[0].media, caption=caption)
        else:
            await message.reply_media_group(group)

        print(f"✅ Sent media for: {tweet_url}")

    except Exception as e:
        await message.reply(f"❌ Telegram error:\n`{e}`")

# ==== Auto-detect tweet links ====
@app.on_message(filters.private & filters.text)
async def detect_link(client: Client, message: Message):
    if "twitter.com" in message.text or "x.com" in message.text:
        message.text = f"/get {message.text}"
        await get_command(client, message)

# ==== Run bot ====
async def main():
    await app.start()
    print("🤖 Bot started...")

    try:
        await app.send_message(ADMIN_ID, "✅ Bot is online and responding to commands.")
    except Exception as e:
        print("⚠️ Couldn't notify admin:", e)

    await idle()

if __name__ == "__main__":
    start_health_check()
    asyncio.run(main())
