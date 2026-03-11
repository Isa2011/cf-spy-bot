import asyncio
import requests
import sqlite3
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8653073291:AAG6jr04iA3i6-_3VXsHjSgXoipZtSC88fM"
OWNER_ID = 7951275068  # твой Telegram ID
CHECK_INTERVAL = 30   # секунд

# ---------- DATABASE ----------

conn = sqlite3.connect("cfbot.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS handles(
    handle TEXT PRIMARY KEY,
    last_submission INTEGER
)
""")

conn.commit()


def is_owner(update: Update):
    return update.effective_user.id == OWNER_ID


# ---------- COMMANDS ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    text = """
🤖 Codeforces Tracker

/add <handle>      — добавить пользователя
/remove <handle>   — удалить
/list              — список
/rating <handle>   — рейтинг
/last <handle>     — последние решения
"""
    await update.message.reply_text(text)


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    if not context.args:
        await update.message.reply_text("Usage: /add handle")
        return

    handle = context.args[0]

    cur.execute(
        "INSERT OR IGNORE INTO handles(handle,last_submission) VALUES(?,0)",
        (handle,)
    )
    conn.commit()

    await update.message.reply_text(f"✅ Added {handle}")


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    if not context.args:
        return

    handle = context.args[0]

    cur.execute("DELETE FROM handles WHERE handle=?", (handle,))
    conn.commit()

    await update.message.reply_text(f"❌ Removed {handle}")


async def list_handles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    cur.execute("SELECT handle FROM handles")
    rows = cur.fetchall()

    if not rows:
        await update.message.reply_text("No handles")
        return

    text = "\n".join([r[0] for r in rows])
    await update.message.reply_text(text)


async def rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    if not context.args:
        return

    handle = context.args[0]

    url = f"https://codeforces.com/api/user.info?handles={handle}"
    data = requests.get(url).json()

    if data["status"] != "OK":
        await update.message.reply_text("User not found")
        return

    u = data["result"][0]

    text = f"""
👤 {handle}

Rating: {u.get("rating","unrated")}
Max: {u.get("maxRating","unrated")}
Rank: {u.get("rank","")}
"""

    await update.message.reply_text(text)


async def last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    if not context.args:
        return

    handle = context.args[0]

    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=5"
    data = requests.get(url).json()

    if data["status"] != "OK":
        await update.message.reply_text("Error")
        return

    text = ""

    for s in data["result"]:
        name = s["problem"]["name"]
        verdict = s.get("verdict","")
        text += f"{name} — {verdict}\n"

    await update.message.reply_text(text)


# ---------- TRACKER ----------

async def tracker(app):

    while True:

        cur.execute("SELECT handle,last_submission FROM handles")
        rows = cur.fetchall()

        for handle, last_id in rows:

            try:

                url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=1"
                data = requests.get(url).json()

                if data["status"] != "OK":
                    continue

                sub = data["result"][0]
                sid = sub["id"]

                if last_id == 0:
                    cur.execute(
                        "UPDATE handles SET last_submission=? WHERE handle=?",
                        (sid, handle)
                    )
                    conn.commit()
                    continue

                if sid != last_id:

                    cur.execute(
                        "UPDATE handles SET last_submission=? WHERE handle=?",
                        (sid, handle)
                    )
                    conn.commit()

                    if sub.get("verdict") == "OK":

                        problem = sub["problem"]["name"]
                        contest = sub["problem"].get("contestId","")

                        msg = f"""
✅ {handle} solved a problem!

Problem: {problem}
Contest: {contest}
"""

                        await app.bot.send_message(
                            chat_id=OWNER_ID,
                            text=msg
                        )

            except:
                pass

        await asyncio.sleep(CHECK_INTERVAL)


# ---------- MAIN ----------

async def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("list", list_handles))
    app.add_handler(CommandHandler("rating", rating))
    app.add_handler(CommandHandler("last", last))

    commands = [
        BotCommand("start","start bot"),
        BotCommand("add","add handle"),
        BotCommand("remove","remove handle"),
        BotCommand("list","list handles"),
        BotCommand("rating","user rating"),
        BotCommand("last","last submissions")
    ]

    await app.bot.set_my_commands(commands)

    asyncio.create_task(tracker(app))

    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
