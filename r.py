import requests
import asyncio
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8653073291:AAG6jr04iA3i6-_3VXsHjSgXoipZtSC88fM"
OWNER_ID = 7951275068  # твой Telegram ID

handles = set()
last_submissions = {}

tracking = True


def is_owner(update: Update):
    return update.effective_user.id == OWNER_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    await update.message.reply_text(
        "🤖 Codeforces Tracker Bot\n"
        "/add handle\n"
        "/remove handle\n"
        "/list\n"
        "/rating handle\n"
        "/last handle\n"
        "/starttrack\n"
        "/stop"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    await start(update, context)


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    if not context.args:
        await update.message.reply_text("Usage: /add handle")
        return

    handle = context.args[0]
    handles.add(handle)
    await update.message.reply_text(f"✅ Added {handle}")


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    if not context.args:
        return

    handle = context.args[0]
    handles.discard(handle)
    await update.message.reply_text(f"❌ Removed {handle}")


async def list_handles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    if not handles:
        await update.message.reply_text("No handles")
        return

    text = "\n".join(handles)
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

    r = data["result"][0]

    text = f"""
👤 {handle}
Rating: {r.get("rating", "unrated")}
Max: {r.get("maxRating", "unrated")}
Rank: {r.get("rank","")}
"""
    await update.message.reply_text(text)


async def last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    handle = context.args[0]

    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=5"
    data = requests.get(url).json()

    res = data["result"]

    text = ""

    for s in res:
        name = s["problem"]["name"]
        verdict = s["verdict"]
        text += f"{name} — {verdict}\n"

    await update.message.reply_text(text)


async def starttrack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global tracking
    if not is_owner(update):
        return
    tracking = True
    await update.message.reply_text("▶ Tracking started")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global tracking
    if not is_owner(update):
        return
    tracking = False
    await update.message.reply_text("⛔ Tracking stopped")


async def tracker(app):
    global last_submissions

    while True:

        if tracking:

            for handle in handles:

                try:

                    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=1"
                    data = requests.get(url).json()

                    if data["status"] != "OK":
                        continue

                    sub = data["result"][0]

                    sid = sub["id"]

                    if handle not in last_submissions:
                        last_submissions[handle] = sid
                        continue

                    if sid != last_submissions[handle]:

                        last_submissions[handle] = sid

                        if sub["verdict"] == "OK":

                            problem = sub["problem"]["name"]
                            contest = sub["problem"].get("contestId", "")

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

        await asyncio.sleep(30)


async def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("list", list_handles))
    app.add_handler(CommandHandler("rating", rating))
    app.add_handler(CommandHandler("last", last))
    app.add_handler(CommandHandler("starttrack", starttrack))
    app.add_handler(CommandHandler("stop", stop))

    asyncio.create_task(tracker(app))

    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
