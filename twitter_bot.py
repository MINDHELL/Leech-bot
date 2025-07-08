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
ADMIN_ID = 6860316927  # Your personal Telegram ID

# === Init ===
app = Client("twitter_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


def extract_from_vxtwitter(tweet_url):
    try:
        tweet_id = tweet_url.split("/status/")[1].split("?")[0]
        api_url = f"https://api.vxtwitter.com/Twitter/status/{tweet_id}"
        r = requests.get(api_url, timeout=10)
        if r.status_code != 200:
            print(f"❌ API Error: {r.status_code}")
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
        print("❌ Extraction error:", e)
        return None, None


@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    await message.reply("👋 Hello! Send a tweet link or use `/get <link>` to download media.")


@app.on_message(filters.command("get") & filters.private)
async def get_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("❗ Please send a tweet link.\nExample:\n`/get https://twitter.com/...`")

    tweet_url = message.command[1]
    caption, media = extract_from_vxtwitter(tweet_url)

    if not media:
        return await message.reply("⚠️ No media found for this tweet.")

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


@app.on_message(filters.text & filters.private)
async def detect_link(client: Client, message: Message):
    if "twitter.com" in message.text or "x.com" in message.text:
        message.text = f"/get {message.text}"
        await get_cmd(client, message)


async def main():
    await app.start()
    print("🤖 Bot started...")

    try:
        await app.send_message(ADMIN_ID, "✅ Bot is now online!")
    except Exception as e:
        print("⚠️ Couldn't notify admin:", e)

    await idle()


if __name__ == "__main__":
    start_health_check()
    asyncio.run(main())
