import threading
from health_check import start_health_check
from pyrogram import Client, filters
import os
import asyncio
from traceback import print_exc
from subprocess import PIPE, STDOUT
from time import time

# Your API credentials
api_id = 27788368
api_hash = "9df7e9ef3d7e4145270045e5e43e1081"
bot_token = "7725707727:AAHojaEgGdbw2a1tkA5L4XueeWtD44AumyM"

bot = Client('m3u8', api_id, api_hash, bot_token=bot_token)

# Optional headers for token-protected .m3u8 links
REFERER = "https://example.com"  # <- Change to real source domain
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

@bot.on_message(filters.command('start'))
async def start(_, message):
    await message.reply(
        '''👋 Welcome to M3U8 Converter Bot!

📥 Send: `/convert <m3u8_link>`

🧠 GitHub: [Lambda Stock](https://github.com/lambda-stock/Telegram-m3u8-Converter/)''',
        disable_web_page_preview=True
    )

@bot.on_message(filters.command(['convert', 'cevir']))
async def convert(client, message):
    try:
        link = message.text.split(' ', 1)[1]
    except:
        print_exc()
        return await message.reply("❌ Usage:\n`/convert <m3u8_link>`")

    _info = await message.reply('🔄 Processing your link...')

    filename = f'{message.from_user.id}_{int(time())}'
    mp4_file = f'{filename}.mp4'
    jpg_file = f'{filename}.jpg'

    # FFmpeg with headers
    ffmpeg_cmd = (
        f'ffmpeg -headers "Referer: {REFERER}\\r\\nUser-Agent: {USER_AGENT}" '
        f'-i "{link}" -c copy -bsf:a aac_adtstoasc "{mp4_file}"'
    )

    await _info.edit("🎞 Converting video to .mp4...")
    proc = await asyncio.create_subprocess_shell(ffmpeg_cmd, stdout=PIPE, stderr=PIPE)
    out, err = await proc.communicate()

    if proc.returncode != 0 or not os.path.exists(mp4_file):
        print(err.decode())
        return await _info.edit("❌ FFmpeg failed:\n" + err.decode().strip())

    await _info.edit('🖼 Generating thumbnail...')
    await asyncio.create_subprocess_shell(
        f'ffmpeg -i "{mp4_file}" -ss 00:00:30.000 -vframes 1 "{jpg_file}"',
        stdout=PIPE, stderr=PIPE
    )

    await _info.edit('⏱ Fetching video duration...')
    proc3 = await asyncio.create_subprocess_shell(
        f'ffprobe -v error -show_entries format=duration '
        f'-of default=noprint_wrappers=1:nokey=1 "{mp4_file}"',
        stdout=PIPE, stderr=STDOUT
    )
    duration_raw, _ = await proc3.communicate()

    try:
        duration = int(float(duration_raw.decode().strip()))
    except:
        duration = None

    await _info.edit("📤 Uploading to Telegram...")

    def progress(current, total):
        print(f"{message.from_user.first_name}: {current}/{total}")

    try:
        await client.send_video(
            message.chat.id,
            mp4_file,
            duration=duration,
            thumb=jpg_file if os.path.exists(jpg_file) else None,
            caption=f"`{filename}.mp4`",
            progress=progress
        )
    except Exception as e:
        print_exc()
        return await _info.edit(f"❌ Upload failed:\n{e}")

    await _info.delete()
    os.remove(mp4_file)
    if os.path.exists(jpg_file):
        os.remove(jpg_file)

# 🔰 Run the Bot
if __name__ == "__main__":
    threading.Thread(target=start_health_check, daemon=True).start()
    bot.run()
