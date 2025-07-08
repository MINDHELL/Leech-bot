import html
import json
import logging
import traceback
import threading
from io import StringIO
from tempfile import TemporaryFile
from urllib.parse import urlsplit

import requests
import telegram.error
from telegram import Update, InputMediaDocument, InputMediaAnimation, constants, BotCommand
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from config import BOT_TOKEN
from health_check import start_health_check

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class APIException(Exception):
    pass


def extract_tweet_ids(text: str):
    """Extract Tweet IDs from Twitter links"""
    import re
    tweet_ids = re.findall(r"(?:twitter|x)\.com/.{1,15}/status/([0-9]{1,20})", text)
    return list(dict.fromkeys(tweet_ids))


def scrape_media(tweet_id: str):
    r = requests.get(f'https://api.vxtwitter.com/Twitter/status/{tweet_id}')
    r.raise_for_status()
    data = r.json()
    if 'media_extended' in data:
        return data['media_extended']
    raise APIException("No media found")


def reply_media(update: Update, context: CallbackContext, media_list: list):
    photos = [m for m in media_list if m["type"] == "image"]
    gifs = [m for m in media_list if m["type"] == "gif"]
    videos = [m for m in media_list if m["type"] == "video"]

    if photos:
        update.message.reply_media_group([
            InputMediaDocument(media=p['url']) for p in photos
        ])
    if gifs:
        for g in gifs:
            update.message.reply_animation(animation=g['url'])
    if videos:
        for v in videos:
            try:
                update.message.reply_video(video=v['url'])
            except:
                update.message.reply_text(f"🔗 {v['url']}")

    context.bot_data.setdefault("media_count", 0)
    context.bot_data["media_count"] += len(media_list)


def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Hi! Send a Twitter/X link and I’ll fetch the media for you.")


def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("📌 Just send any Twitter or X link with media.")


def stats_command(update: Update, context: CallbackContext):
    count = context.bot_data.get("media_count", 0)
    update.message.reply_text(f"📊 Media sent so far: {count}")


def reset_stats(update: Update, context: CallbackContext):
    context.bot_data["media_count"] = 0
    update.message.reply_text("✅ Stats reset.")


def handle_text(update: Update, context: CallbackContext):
    text = update.message.text
    tweet_ids = extract_tweet_ids(text)

    if not tweet_ids:
        update.message.reply_text("⚠️ No tweet found in your message.")
        return

    for tweet_id in tweet_ids:
        try:
            media = scrape_media(tweet_id)
            reply_media(update, context, media)
        except Exception as e:
            update.message.reply_text(f"❌ Failed to fetch media: {str(e)}")


def error_handler(update, context: CallbackContext):
    logger.error(msg="Exception while handling update:", exc_info=context.error)
    if update and update.effective_message:
        update.effective_message.reply_text("⚠️ An unexpected error occurred.")


def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("stats", stats_command))
    dp.add_handler(CommandHandler("resetstats", reset_stats))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    dp.add_error_handler(error_handler)

    updater.bot.set_my_commands([
        BotCommand("start", "Start the bot"),
        BotCommand("help", "How to use the bot"),
        BotCommand("stats", "Show usage stats"),
        BotCommand("resetstats", "Reset stats")
    ])

    threading.Thread(target=start_health_check, daemon=True).start()
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
