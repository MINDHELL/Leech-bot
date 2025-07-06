import threading
from health_check import start_health_check
import os
import asyncio
import re
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = 27788368
API_HASH = "9df7e9ef3d7e4145270045e5e43e1081"
BOT_TOKEN = "7725707727:AAHojaEgGdbw2a1tkA5L4XueeWtD44AumyM"

bot = Client("video_universal_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

progress_pattern = re.compile(r"(\d{1,3}\.\d)%.*?at\s+([\d\.]+[KMG]?iB/s).*?ETA\s+([\d:]+)")

@bot.on_message(filters.command("start"))
async def start(_, msg: Message):
    await msg.reply(
        "🎬 *Send a `.m3u8` or direct `.mp4` link to download video.*\n\n"
        "**Optional format:**\n"
        "`URL: <link>`\n"
        "`Referer: <ref>` (optional)\n"
        "`User-Agent: <ua>` (optional)",
        quote=True
    )

@bot.on_message(filters.text & filters.private)
async def process(_, msg: Message):
    text = msg.text.strip()
    lines = text.splitlines()

    url = referer = user_agent = None

    for line in lines:
        if ("m3u8" in line or "mp4" in line) and line.startswith("http"):
            url = line.strip()
        elif line.lower().startswith("url:"):
            url = line.split(":", 1)[1].strip()
        elif line.lower().startswith("referer:"):
            referer = line.split(":", 1)[1].strip()
        elif line.lower().startswith("user-agent:"):
            user_agent = line.split(":", 1)[1].strip()

    if not url:
        return await msg.reply("❌ Please provide a valid `.mp4` or `.m3u8` link.")

    progress_msg = await msg.reply("⏳ Starting download...")

    try:
        output_file = "video.mp4"

        # ✅ Use yt-dlp for .m3u8
        if ".m3u8" in url:
            command = ["yt-dlp", "-o", output_file]
            if referer:
                command += ["--referer", referer]
            if user_agent:
                command += ["--user-agent", user_agent]
            command.append(url)

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                decoded = line.decode(errors="ignore").strip()
                match = progress_pattern.search(decoded)
                if match:
                    percent, speed, eta = match.groups()
                    try:
                        await progress_msg.edit(
                            f"⬇️ Downloading...\n"
                            f"📊 {percent}% at {speed}\n"
                            f"⏱ ETA: {eta}"
                        )
                    except:
                        pass

            await process.wait()

        # ✅ Use aiohttp for .mp4 direct links
        elif ".mp4" in url:
            headers = {}
            if referer:
                headers["Referer"] = referer
            if user_agent:
                headers["User-Agent"] = user_agent

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return await progress_msg.edit(f"❌ Failed to fetch: HTTP {response.status}")

                    total = int(response.headers.get("Content-Length", 0))
                    if total >= 1900 * 1024 * 1024:
                        return await progress_msg.edit("⚠️ File too large for Telegram (limit ~1.9 GB)")

                    with open(output_file, "wb") as f:
                        downloaded = 0
                        chunk_size = 1024 * 512
                        while True:
                            chunk = await response.content.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            percent = downloaded * 100 / total if total else 0
                            try:
                                await progress_msg.edit(f"⬇️ Downloading MP4...\n📊 {percent:.1f}%")
                            except:
                                pass

        if not os.path.exists(output_file):
            return await progress_msg.edit("❌ Download failed.")

        await progress_msg.edit("📤 Uploading video...")
        await msg.reply_video(output_file, caption="✅ Here's your video!")
        os.remove(output_file)

    except Exception as e:
        try:
            await progress_msg.edit(f"⚠️ Error:\n`{str(e)[:3000]}`")
        except:
            await msg.reply(f"⚠️ Fatal error:\n`{str(e)[:3000]}`")

# ✅ Start health check + run bot
if __name__ == "__main__":
    threading.Thread(target=start_health_check, daemon=True).start()
    bot.run()
