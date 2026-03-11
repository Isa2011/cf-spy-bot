# r.py
import asyncio
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ====== Настройки ======
TOKEN = "8653073291:AAG6jr04iA3i6-_3VXsHjSgXoipZtSC88fM"  # <-- вставь свой токен
OWNER_ID = 7951275068  # <-- твой Telegram ID
CF_USER = "whyy"  # <-- твой Codeforces ник
CHECK_INTERVAL = 60  # секунды между проверкой новых решений

last_submission_id = None

# ====== Проверка главного ======
def is_owner(update: Update):
    return update.effective_user.id == OWNER_ID

# ====== Команды ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("⛔️ Эта команда доступна только главному")
        return
    keyboard = [
        [InlineKeyboardButton("Последние решения", callback_data="last")],
        [InlineKeyboardButton("Статистика", callback_data="stats")],
        [InlineKeyboardButton("Топ", callback_data="top")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Привет, {CF_USER}! Это твой личный бот 🐱‍💻", reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("⛔️ Эта команда доступна только главному")
        return
    await update.message.reply_text(
        "/start - Главное меню\n"
        "/last - Последние решения\n"
        "/stats - Статистика\n"
        "/top - Топ проблем\n"
        "/help - Список команд"
    )

async def last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("⛔️ Эта команда доступна только главному")
        return
    url = f"https://codeforces.com/api/user.status?handle={CF_USER}&from=1&count=5"
    r = requests.get(url).json()
    if r["status"] != "OK":
        await update.message.reply_text("Ошибка при получении данных CF")
        return
    text = ""
    for sub in r["result"]:
        pid = sub["problem"]["contestId"]
        name = sub["problem"]["name"]
        verdict = sub.get("verdict", "UNKNOWN")
        text += f"{pid} - {name}: {verdict}\n"
    await update.message.reply_text(text)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("⛔️ Эта команда доступна только главному")
        return
    url = f"https://codeforces.com/api/user.info?handles={CF_USER}"
    r = requests.get(url).json()
    if r["status"] != "OK":
        await update.message.reply_text("Ошибка при получении данных CF")
        return
    user = r["result"][0]
    await update.message.reply_text(
        f"Ник: {user['handle']}\n"
        f"Рейтинг: {user.get('rating', 'N/A')}\n"
        f"Макс рейтинг: {user.get('maxRating', 'N/A')}\n"
        f"Ранг: {user.get('rank', 'N/A')}\n"
        f"Макс ранг: {user.get('maxRank', 'N/A')}"
    )

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("⛔️ Эта команда доступна только главному")
        return
    await update.message.reply_text("Эта команда в разработке...")

# ====== Основной запуск бота ======
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("last", last))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("top", top))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
