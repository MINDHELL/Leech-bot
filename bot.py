import threading
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN
from yt_dlp import YoutubeDL
from health_check import start_health_check

bot = Client("leech_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.private & filters.command("start"))
async def start(_, message: Message):
    await message.reply_text("👋 Send me a video URL (YouTube, etc.), and I'll fetch it for you!")

@bot.on_message(filters.private & filters.text & ~filters.command(["start"]))
async def download_and_send(_, message: Message):
    url = message.text.strip()

    await message.reply_text("🔄 Downloading...")

    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
        'max_filesize': 2 * 1024 * 1024 * 1024,  # 2 GB limit
        'merge_output_format': 'mp4',
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")
        return

    await message.reply_text("📤 Uploading...")
    try:
        await message.reply_video(file_path, caption="✅ Here's your video!")
    except Exception as e:
        await message.reply_text(f"❌ Upload failed: {e}")
    finally:
        os.remove(file_path)

# 🔰 Run the Bot
if __name__ == "__main__":
    threading.Thread(target=start_health_check, daemon=True).start()
    bot.run()
