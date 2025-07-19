import os
import asyncio
import time
import threading
from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN
from yt_dlp import YoutubeDL
from health_check import start_health_check
import ffmpeg

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

                asyncio.run_coroutine_threadsafe(status_msg.edit_text(msg), bot.loop)
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


def extract_thumbnail(video_path, thumb_path="thumb.jpg"):
    try:
        (
            ffmpeg
            .input(video_path, ss=3)
            .output(thumb_path, vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return thumb_path if os.path.exists(thumb_path) else None
    except Exception:
        return None


@bot.on_message(filters.private & filters.command("start"))
async def start(_, message: Message):
    await message.reply_text("👋 Send me a video URL (YouTube, m3u8, etc.), and I'll fetch it for you!")


@bot.on_message(filters.private & filters.text & ~filters.command(["start"]))
async def download_and_send(_, message: Message):
    url = message.text.strip()
    if not url.startswith("http"):
        await message.reply("❌ Please send a valid video URL starting with http/https.")
        return

    status = await message.reply_text("🔄 Preparing to download...")

    os.makedirs("downloads", exist_ok=True)
    output_template = "downloads/%(title)s.%(ext)s"

    ydl_opts = {
        'outtmpl': output_template,
        'format': 'bestvideo+bestaudio/best',
        'max_filesize': 2 * 1024 * 1024 * 1024,  # 2GB
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'progress_hooks': [create_download_hook(status)],
        'retries': 3,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }

    file_path = None
    thumb_path = "thumb.jpg"

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        if not os.path.exists(file_path):
            await status.edit_text("❌ Failed to download the video file.")
            return

        if os.path.getsize(file_path) > 2 * 1024 * 1024 * 1024:
            await status.edit_text("⚠️ File too large (over 2GB). Telegram bots can't upload.")
            os.remove(file_path)
            return

        # Generate thumbnail
        thumb_path = extract_thumbnail(file_path)

    except Exception as e:
        await status.edit_text(f"❌ Download error: `{e}`")
        return

    await status.edit_text("📤 Uploading...")

    try:
        await message.reply_video(
            video=file_path,
            caption="✅ Here's your video!",
            thumb=thumb_path if thumb_path and os.path.exists(thumb_path) else None,
            supports_streaming=True,
            progress=upload_progress,
            progress_args=(status,)
        )
    except Exception as e:
        await status.edit_text(f"❌ Upload failed: `{e}`")
    finally:
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
        except:
            pass


if __name__ == "__main__":
    threading.Thread(target=start_health_check, daemon=True).start()
    bot.run()
