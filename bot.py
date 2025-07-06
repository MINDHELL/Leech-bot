import threading
from health_check import start_health_check
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import subprocess

# 🔐 Replace with your details
API_ID = 27788368
API_HASH = "9df7e9ef3d7e4145270045e5e43e1081"
BOT_TOKEN = "7725707727:AAHojaEgGdbw2a1tkA5L4XueeWtD44AumyM"

bot = Client("m3u8_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start(_, msg: Message):
    await msg.reply("🎥 Send me a `.m3u8` link and I'll download & send the video.")

@bot.on_message(filters.text & filters.private)
async def download_m3u8(_, msg: Message):
    m3u8_url = msg.text.strip()

    if not m3u8_url.endswith(".m3u8"):
        return await msg.reply("❌ Please send a valid `.m3u8` link.")

    await msg.reply("⏬ Downloading and processing... Please wait.")

    try:
        output_file = "video.mp4"

        command = [
            "yt-dlp",
            "--referer", "https://www.xnxx.com/",
            "--user-agent", "Mozilla/5.0",
            "-o", output_file,
            m3u8_url
        ]

        process = await asyncio.create_subprocess_exec(*command)
        await process.communicate()

        if not os.path.exists(output_file):
            return await msg.reply("❌ Failed to download the video.")

        await msg.reply_video(output_file, caption="✅ Here's your video!")

        os.remove(output_file)

    except Exception as e:
        await msg.reply(f"⚠️ Error:\n`{e}`")

# 🔰 Run the Bot
if __name__ == "__main__":
    threading.Thread(target=start_health_check, daemon=True).start()
    bot.run()
