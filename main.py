import os
import re
import asyncio
from decimal import Decimal, InvalidOperation
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing")

flask_app = Flask(__name__)
tg_app = Application.builder().token(BOT_TOKEN).build()

MATH_PATTERN = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*([\+\-\*/])\s*(-?\d+(?:\.\d+)?)\s*$")

def format_decimal(value: Decimal) -> str:
    if value == value.to_integral():
        return str(int(value))
    return format(value.normalize(), "f").rstrip("0").rstrip(".")

def calculate_expression(text: str):
    m = MATH_PATTERN.fullmatch(text.strip())
    if not m:
        return None

    a_str, op, b_str = m.groups()

    try:
        a = Decimal(a_str)
        b = Decimal(b_str)
    except InvalidOperation:
        return None

    if op == "+":
        r = a + b
    elif op == "-":
        r = a - b
    elif op == "*":
        r = a * b
    elif op == "/":
        if b == 0:
            return "0 diye vag kora jabe na"
        r = a / b
    else:
        return None

    return format_decimal(r)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Calculator bot ready")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    result = calculate_expression(update.message.text)
    if result is not None:
        await update.message.reply_text(result)

tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

@flask_app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200

@flask_app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), tg_app.bot)
    asyncio.run(tg_app.initialize())
    asyncio.run(tg_app.process_update(update))
    return "ok", 200
