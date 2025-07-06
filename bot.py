import threading
from health_check import start_health_check
import os
import asyncio
import re
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = 27788368
API_HASH = "9df7e9ef3d7e4145270045e5e43e1081"
BOT_TOKEN = "7725707727:AAHojaEgGdbw2a1tkA5L4XueeWtD44AumyM"

bot = Client("m3u8_universal_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

progress_pattern = re.compile(r"(\d{1,3}\.\d)%.*?at\s+([\d\.]+[KMG]?iB/s).*?ETA\s+([\d:]+)")

@bot.on_message(filters.command("start"))
async def start(_, msg: Message):
    await msg.reply(
        "🎬 *Send a `.m3u8` link to download video.*\n\n"
        "**Format:**\n"
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
        if "m3u8" in line and line.startswith("http"):
            url = line.strip()
        elif line.lower().startswith("url:"):
            url = line.split(":", 1)[1].strip()
        elif line.lower().startswith("referer:"):
            referer = line.split(":", 1)[1].strip()
        elif line.lower().startswith("user-agent:"):
            user_agent = line.split(":", 1)[1].strip()

    if not url or "m3u8" not in url:
        return await msg.reply("❌ Please provide a valid `.m3u8` link.")

    progress_msg = await msg.reply("⏳ Starting download...")

    try:
        output_file = "video.mp4"
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

        collected_output = ""
        while True:
            line = await process.stdout.readline()
            if not line:
                break

            decoded = line.decode(errors="ignore").strip()
            collected_output += decoded + "\n"

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
                    pass  # ignore Telegram message too long issues

        await process.wait()

        if process.returncode != 0 or not os.path.exists(output_file):
            # Send output in parts if failed
            error_chunks = [collected_output[i:i+3000] for i in range(0, len(collected_output), 3000)]
            await progress_msg.edit("❌ Download failed. Sending log...")
            for i, chunk in enumerate(error_chunks[:3]):
                await msg.reply(f"⚠️ Error Log Part {i+1}:\n{chunk}", quote=False)
            return

        if os.path.getsize(output_file) >= 1900 * 1024 * 1024:
            return await progress_msg.edit("⚠️ Video too large (>1.9GB). Telegram upload may fail. Compress or split first.")

        await progress_msg.edit("📤 Uploading video...")
        await msg.reply_video(output_file, caption="✅ Here's your video!")

        os.remove(output_file)

    except Exception as e:
        await progress_msg.edit(f"⚠️ Error:\n`{str(e)[:3000]}`")



# 🔰 Run the Bot
if __name__ == "__main__":
    threading.Thread(target=start_health_check, daemon=True).start()
    bot.run()
