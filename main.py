import os
import re
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing")

MATH_PATTERN = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*([\+\-\*/])\s*(-?\d+(?:\.\d+)?)\s*$")

flask_app = Flask(__name__)
tg_app = Application.builder().token(BOT_TOKEN).build()


def calculate_expression(text: str):
    match = MATH_PATTERN.fullmatch(text.strip())
    if not match:
        return None

    a_str, op, b_str = match.groups()
    a = float(a_str)
    b = float(b_str)

    if op == "+":
        result = a + b
    elif op == "-":
        result = a - b
    elif op == "*":
        result = a * b
    elif op == "/":
        if b == 0:
            return "0 diye vag kora jabe na"
        result = a / b
    else:
        return None

    if result.is_integer():
        return str(int(result))
    return str(result)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "Calculator bot ready.\n\nExamples:\n2+2\n13-3\n2*2\n8/2"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    if update.effective_chat and update.effective_chat.type not in ("group", "supergroup", "private"):
        return

    text = update.message.text.strip()

    # private chat এ /start ছাড়া normal expression-ও কাজ করবে
    result = calculate_expression(text)
    if result is not None:
        await update.message.reply_text(result)


@flask_app.get("/")
def healthcheck():
    return "Bot is running", 200


@flask_app.post(f"/{BOT_TOKEN}")
def telegram_webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, tg_app.bot)
    asyncio.run(tg_app.process_update(update))
    return "ok", 200


async def startup():
    await tg_app.initialize()
    await tg_app.start()
    if WEBHOOK_URL:
        webhook_target = f"{WEBHOOK_URL.rstrip('/')}/{BOT_TOKEN}"
        await tg_app.bot.set_webhook(webhook_target)
        logger.info("Webhook set to %s", webhook_target)


tg_app.add_handler(CommandHandler("start", start_command))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

asyncio.run(startup())
