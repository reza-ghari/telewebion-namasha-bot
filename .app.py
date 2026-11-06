
import os
import asyncio
import tempfile
from pathlib import Path

from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import yt_dlp

TOKEN = os.environ.get("BOT_TOKEN")

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! لینک دانلود مستقیم تلوبیون را بفرست."
    )

def download_video(url, folder):
    options = {
        "outtmpl": str(Path(folder) / "%(title).100s.%(ext)s"),
        "format": "best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    return filename, info.get("title", "ویدئو")

async def receive_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    url = update.message.text.strip()

    if not url.startswith("https://"):
        await update.message.reply_text("لطفاً لینک معتبر بفرست.")
        return

    await update.message.reply_text("در حال دریافت ویدئو...")

    try:
        with tempfile.TemporaryDirectory() as folder:
            filename, title = await asyncio.to_thread(
                download_video, url, folder
            )

            size = os.path.getsize(filename) / (1024 * 1024)

            await update.message.reply_text(
                f"دانلود با موفقیت انجام شد.\n"
                f"عنوان: {title}\n"
                f"حجم: {size:.1f} MB\n\n"
                f"مرحله بعد: اتصال به آپلود نماشا."
            )

    except Exception as error:
        await update.message.reply_text(
            f"خطا در دریافت ویدئو:\n{str(error)[:800]}"
        )

async def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN تنظیم نشده است.")

    bot = Application.builder().token(TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link)
    )

    await bot.initialize()
    await bot.start()
    await bot.updater.start_polling()

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    import threading

    threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 10000))
        ),
        daemon=True
    ).start()

    asyncio.run(main())
