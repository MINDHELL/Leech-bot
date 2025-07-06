import threading
from health_check import start_health_check
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from yt_dlp import YoutubeDL

API_ID = 27788368
API_HASH = "9df7e9ef3d7e4145270045e5e43e1081"
BOT_TOKEN = "7725707727:AAHojaEgGdbw2a1tkA5L4XueeWtD44AumyM"

bot = Client("m3u8_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DOWNLOAD_DIR = "downloads"

@bot.on_message(filters.private & filters.command("start"))
async def start(_, message: Message):
    await message.reply_text("👋 Send me a `.m3u8` link and I’ll fetch the video for you.")

@bot.on_message(filters.private & filters.text & ~filters.command("start"))
async def download_m3u8(_, message: Message):
    url = message.text.strip()

    if not url.endswith(".m3u8"):
        return await message.reply("❌ Please send a valid `.m3u8` link.")

    status = await message.reply("🔄 Starting download...")

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    filename = f"{message.from_user.id}_{message.id}.mp4"
    output_path = os.path.join(DOWNLOAD_DIR, filename)

    ydl_opts = {
        'outtmpl': output_path,
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [lambda d: asyncio.create_task(hook(d, status))],
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return await status.edit(f"❌ Error:\n`{e}`")

    if os.path.getsize(output_path) > 2 * 1024 * 1024 * 1024:
        return await status.edit("❌ File too large (>2GB) for Telegram.")

    await status.edit("✅ Uploading...")
    await message.reply_video(output_path, caption="🎥 Here's your video!")
    await status.delete()
    os.remove(output_path)

async def hook(d, status_msg):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '').strip()
        speed = d.get('_speed_str', '').strip()
        eta = d.get('eta', 'N/A')
        await status_msg.edit(f"⬇️ Downloading...\n📊 {percent} at {speed}\n⏱ ETA: {eta}s")
    elif d['status'] == 'finished':
        await status_msg.edit("✅ Download finished. Uploading...")

# 🔰 Run the Bot
if __name__ == "__main__":
    threading.Thread(target=start_health_check, daemon=True).start()
    bot.run()
