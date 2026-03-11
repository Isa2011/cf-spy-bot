import logging
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio

# ========== Настройки ==========
TOKEN = "8653073291:AAG6jr04iA3i6-_3VXsHjSgXoipZtSC88fM"
OWNER_ID = 7951275068  # твой Telegram ID
CODEFORCES_HANDLE = "whyy"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ========== Приватная проверка ==========
def is_owner(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("⛔️ Эта команда доступна только главному")
            return
        return await func(update, context)
    return wrapper

# ========== Меню ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Codeforces", callback_data="cf")],
        [InlineKeyboardButton("Рандом", callback_data="random")],
        [InlineKeyboardButton("Шутка", callback_data="joke")],
        [InlineKeyboardButton("Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Привет, {update.effective_user.first_name}! Это твой приватный бот.",
        reply_markup=reply_markup
    )

# ========== Callback для меню ==========
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cf":
        rating = get_cf_rating(CODEFORCES_HANDLE)
        await query.edit_message_text(f"💻 {CODEFORCES_HANDLE} — рейтинг: {rating}")
    elif query.data == "random":
        import random
        await query.edit_message_text(f"🎲 Случайное число: {random.randint(1,100)}")
    elif query.data == "joke":
        await query.edit_message_text("😂 Почему программисты любят темноту? Потому что свет привлекает баги!")
    elif query.data == "help":
        await query.edit_message_text("""
Доступные команды:
/start - Главное меню
/cf - Рейтинг Codeforces
/random - Случайное число
/joke - Шутка
/help - Список команд
""")

# ========== Команды ==========
@is_owner
async def cf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rating = get_cf_rating(CODEFORCES_HANDLE)
    await update.message.reply_text(f"💻 {CODEFORCES_HANDLE} — рейтинг: {rating}")

@is_owner
async def random_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import random
    await update.message.reply_text(f"🎲 Случайное число: {random.randint(1,100)}")

@is_owner
async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("😂 Почему программисты любят темноту? Потому что свет привлекает баги!")

@is_owner
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
Доступные команды:
/start - Главное меню
/cf - Рейтинг Codeforces
/random - Случайное число
/joke - Шутка
/help - Список команд
""")

# ========== Codeforces API ==========
def get_cf_rating(handle):
    try:
        r = requests.get(f"https://codeforces.com/api/user.info?handles={handle}").json()
        if r["status"] == "OK":
            user = r["result"][0]
            return user.get("rating", "—")
        return "не найдено"
    except:
        return "ошибка"

# ========== Основной запуск ==========
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cf", cf))
    app.add_handler(CommandHandler("random", random_cmd))
    app.add_handler(CommandHandler("joke", joke))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(button))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
