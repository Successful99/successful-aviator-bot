import os
import sqlite3
import logging
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
DB_PATH = os.environ.get("DB_PATH", "aviator_bot.db")
BROADCAST_HOURS = int(os.environ.get("BROADCAST_HOURS", "6"))

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

DISCLAIMER = (
    "⚠️ These are examples and historical records, not predictions. "
    "Aviator crash points cannot be reliably predicted. Only play with "
    "money you can afford to lose."
)


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            chat_id INTEGER PRIMARY KEY,
            subscribed_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            multiplier REAL NOT NULL,
            recorded_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    with connect_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO subscribers(chat_id, subscribed_at) VALUES (?, ?)",
            (chat_id, now_iso()),
        )
    await update.effective_message.reply_text(
        "✈️ Welcome to SUCCESSFUL AVIATOR BOT!\n\n"
        "I provide sample cash-out calculations and record multipliers you enter. "
        "I do not predict future crashes.\n\n"
        "Commands:\n"
        "/guide — sample cash-out targets for a ₦100 stake\n"
        "/record 1.42 — record a round multiplier\n"
        "/stats — statistics for your recorded rounds\n"
        "/subscribe — receive scheduled reminders\n"
        "/unsubscribe — stop scheduled reminders\n"
        "/help — show commands\n\n"
        + DISCLAIMER
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Commands:\n"
        "/start — start the bot\n"
        "/guide — sample payout guide for a ₦100 stake\n"
        "/record MULTIPLIER — save a multiplier, e.g. /record 1.42\n"
        "/stats — show statistics from your saved records\n"
        "/subscribe — opt in to scheduled reminders\n"
        "/unsubscribe — opt out of scheduled reminders\n"
        "/help — show this help\n\n"
        "Recorded history is not a prediction of future rounds."
    )


async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🎯 SAMPLE CASH-OUT GUIDE — ₦100 stake\n\n"
        "1.50× → ₦150 total payout; ₦50 net profit if successful\n"
        "1.75× → ₦175 total payout; ₦75 net profit if successful\n"
        "2.00× → ₦200 total payout; ₦100 net profit if successful\n\n"
        "If the round crashes before cash-out, you generally lose the ₦100 stake.\n"
        "These are payout examples, not signals or predictions.\n\n" + DISCLAIMER
    )


async def record_round(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.effective_message.reply_text(
            "Use /record MULTIPLIER, for example: /record 1.42"
        )
        return
    try:
        multiplier = float(context.args[0].lower().replace("x", ""))
    except ValueError:
        await update.effective_message.reply_text("Please enter a number, e.g. /record 1.42")
        return
    if multiplier < 1.0 or multiplier > 1_000_000:
        await update.effective_message.reply_text("Enter a multiplier of at least 1.00.")
        return

    chat_id = update.effective_chat.id
    with connect_db() as conn:
        conn.execute(
            "INSERT INTO rounds(chat_id, multiplier, recorded_at) VALUES (?, ?, ?)",
            (chat_id, multiplier, now_iso()),
        )
    await update.effective_message.reply_text(
        f"Saved recorded multiplier: {multiplier:.2f}×\n"
        "This is a historical entry, not a prediction."
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    with connect_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*), AVG(multiplier), MIN(multiplier), MAX(multiplier) "
            "FROM rounds WHERE chat_id = ?",
            (chat_id,),
        ).fetchone()
        last_rows = conn.execute(
            "SELECT multiplier, recorded_at FROM rounds WHERE chat_id = ? "
            "ORDER BY id DESC LIMIT 5",
            (chat_id,),
        ).fetchall()

    count, avg, low, high = row
    if count == 0:
        await update.effective_message.reply_text(
            "No rounds recorded yet.\nExample: /record 1.42"
        )
        return

    recent = "\n".join(f"• {m:.2f}× — {t}" for m, t in last_rows)
    await update.effective_message.reply_text(
        "📊 YOUR RECORDED HISTORY\n\n"
        f"Rounds recorded: {count}\n"
        f"Average multiplier: {avg:.2f}×\n"
        f"Lowest recorded: {low:.2f}×\n"
        f"Highest recorded: {high:.2f}×\n\n"
        f"Most recent entries (UTC):\n{recent}\n\n"
        "Past results do not reliably predict future crashes."
    )


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    with connect_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO subscribers(chat_id, subscribed_at) VALUES (?, ?)",
            (chat_id, now_iso()),
        )
    await update.effective_message.reply_text(
        f"✅ Scheduled reminders enabled. I will send a reminder approximately every "
        f"{BROADCAST_HOURS} hours while the bot is online.\n"
        "Use /unsubscribe to stop them.\n\n" + DISCLAIMER
    )


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    with connect_db() as conn:
        conn.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
    await update.effective_message.reply_text("Scheduled reminders stopped for this chat.")


async def send_scheduled_reminder(context: ContextTypes.DEFAULT_TYPE):
    with connect_db() as conn:
        chat_ids = [r[0] for r in conn.execute("SELECT chat_id FROM subscribers").fetchall()]

    message = (
        "✈️ SUCCESSFUL AVIATOR BOT — scheduled reminder\n\n"
        "Sample targets are examples only; they are not signals:\n"
        "• 1.50× on ₦100 = ₦150 total payout if reached\n"
        "• 1.75× on ₦100 = ₦175 total payout if reached\n"
        "• 2.00× on ₦100 = ₦200 total payout if reached\n\n"
        + DISCLAIMER
    )
    for chat_id in chat_ids:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
        except Exception:
            log.exception("Could not send scheduled message to chat %s", chat_id)


async def post_init(application: Application):
    application.job_queue.run_repeating(
        send_scheduled_reminder,
        interval=BROADCAST_HOURS * 60 * 60,
        first=BROADCAST_HOURS * 60 * 60,
        name="scheduled_reminders",
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("Missing BOT_TOKEN environment variable. Set it in your hosting dashboard.")
    connect_db()
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("guide", guide))
    application.add_handler(CommandHandler("record", record_round))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
