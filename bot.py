import threading
import os
import asyncio
import re
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = 27788368
API_HASH = "9df7e9ef3d7e4145270045e5e43e1081"
BOT_TOKEN = "7725707727:AAHojaEgGdbw2a1tkA5L4XueeWtD44AumyM"

bot = Client("final_m3u8_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
progress_pattern = re.compile(r"(\d{1,3}\.\d)%.*?at\s+([\d\.]+[KMG]?iB/s).*?ETA\s+([\d:]+)")

@bot.on_message(filters.command("start"))
async def start(_, msg: Message):
    await msg.reply(
        "📥 *Send a .m3u8 or .mp4 link to download.*\n\n"
        "🔹 Format:\n"
        "`URL: <link>`\n"
        "`Referer: <ref>` (optional)\n"
        "`User-Agent: <ua>` (optional)",
        quote=True
    )

@bot.on_message(filters.text & filters.private)
async def process(_, msg: Message):
    try:
        text = msg.text.strip()
        url = referer = user_agent = None
        for line in text.splitlines():
            if ("http" in line and (".m3u8" in line or ".mp4" in line)):
                url = line.strip()
            elif line.lower().startswith("url:"):
                url = line.split(":", 1)[1].strip()
            elif line.lower().startswith("referer:"):
                referer = line.split(":", 1)[1].strip()
            elif line.lower().startswith("user-agent:"):
                user_agent = line.split(":", 1)[1].strip()

        if not url:
            return await msg.reply("❌ No valid URL provided.")

        output = "video.mp4"
        if os.path.exists(output):
            os.remove(output)

        progress = await msg.reply("🔄 Starting...")

        if ".mp4" in url:
            await download_mp4(url, output, referer, user_agent, progress)
        elif ".m3u8" in url:
            await download_m3u8(url, output, referer, user_agent, progress)

        if not os.path.exists(output):
            return await progress.edit("❌ Download failed.")

        await progress.edit("📤 Uploading to Telegram...")
        await msg.reply_video(output, caption="✅ Here's your video!")
        os.remove(output)

    except Exception as e:
        await msg.reply(f"⚠️ Error:\n`{str(e)[:4000]}`")

async def download_mp4(url, output_file, referer, user_agent, progress_msg):
    headers = {}
    if referer:
        headers["Referer"] = referer
    if user_agent:
        headers["User-Agent"] = user_agent
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as r:
            if r.status != 200:
                await progress_msg.edit(f"❌ MP4 link error: HTTP {r.status}")
                return
            total = int(r.headers.get("Content-Length", 0))
            if total > 1900 * 1024 * 1024:
                await progress_msg.edit("❌ File too big for Telegram (2GB limit).")
                return
            with open(output_file, "wb") as f:
                done = 0
                while True:
                    chunk = await r.content.read(1024 * 512)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    try:
                        percent = done * 100 / total
                        await progress_msg.edit(f"⬇️ Downloading MP4...\n📊 {percent:.1f}%")
                    except:
                        pass

async def download_m3u8(url, output_file, referer, user_agent, progress_msg):
    command = ["yt-dlp", "-o", output_file, "--no-check-certificate"]
    if referer:
        command += ["--referer", referer]
    if user_agent:
        command += ["--user-agent", user_agent]
    command.append(url)
    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        decoded = line.decode(errors="ignore").strip()
        match = progress_pattern.search(decoded)
        if match:
            percent, speed, eta = match.groups()
            try:
                await progress_msg.edit(f"⬇️ Downloading M3U8...\n📊 {percent}% at {speed}\n⏱ ETA: {eta}")
            except:
                pass
    await proc.wait()

if __name__ == "__main__":
    def dummy_health(): pass
    threading.Thread(target=dummy_health, daemon=True).start()
    bot.run()
