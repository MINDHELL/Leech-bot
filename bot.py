import os
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN
from yt_dlp import YoutubeDL
from health_check import start_health_check
import threading

bot = Client("leech_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


def human_readable_size(size):
    if not size:
        return "0B"
    power = 1024
    n = 0
    Dic_powerN = {0: '', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return f"{round(size, 2)} {Dic_powerN[n]}B"


def generate_progress_bar(percentage):
    filled_length = int(percentage // 10)
    bar = '▰' * filled_length + '▱' * (10 - filled_length)
    return f"[{bar}] {percentage:.2f}%"


def create_download_hook(status_msg: Message):
    last_edit = time.time()

    def hook(d):
        nonlocal last_edit
        if d['status'] == 'downloading':
            now = time.time()
            if now - last_edit >= 2:
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes", 0) or d.get("total_bytes_estimate", 0)
                percent = (downloaded / total * 100) if total else 0
                bar = generate_progress_bar(percent)
                size_text = f"{human_readable_size(downloaded)} / {human_readable_size(total)}"
                speed = d.get('_speed_str', 'N/A').strip()
                eta = d.get('_eta_str', 'N/A').strip()

                msg = (
                    f"📥 **Downloading...**\n\n"
                    f"{bar}\n"
                    f"Size: **{size_text}**\n"
                    f"Speed: **{speed}**\n"
                    f"ETA: **{eta}**"
                )

                asyncio.create_task(status_msg.edit_text(msg))
                last_edit = now

    return hook


async def upload_progress(current, total, status_msg: Message):
    try:
        percent = (current / total) * 100
        bar = generate_progress_bar(percent)
        size = f"{human_readable_size(current)} / {human_readable_size(total)}"

        msg = (
            f"📤 **Uploading...**\n\n"
            f"{bar}\n"
            f"Size: **{size}**"
        )
        await status_msg.edit_text(msg)
    except:
        pass


@bot.on_message(filters.private & filters.command("start"))
async def start(_, message: Message):
    await message.reply_text("👋 Send me a video URL (YouTube, etc.), and I'll fetch it for you!")


@bot.on_message(filters.private & filters.text & ~filters.command(["start"]))
async def download_and_send(_, message: Message):
    url = message.text.strip()
    status = await message.reply_text("🔄 Preparing to download...")

    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
        'max_filesize': 2 * 1024 * 1024 * 1024,
        'merge_output_format': 'mp4',
        'progress_hooks': [create_download_hook(status)],
        'noplaylist': True
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
    except Exception as e:
        await status.edit_text(f"❌ Download error: `{e}`")
        return

    await status.edit_text("📤 Uploading...")
    try:
        await message.reply_video(file_path, caption="✅ Here's your video!", progress=upload_progress, progress_args=(status,))
    except Exception as e:
        await status.edit_text(f"❌ Upload failed: `{e}`")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# 🔰 Run the Bot
if __name__ == "__main__":
    threading.Thread(target=start_health_check, daemon=True).start()
    bot.run()
