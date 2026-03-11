import logging
import random
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

TOKEN = "8653073291:AAG6jr04iA3i6-_3VXsHjSgXoipZtSC88fM"
OWNER_ID = 7951275068  # твой Telegram ID
CODEFORCES_HANDLE = "whyy"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()
import asyncio

# Очистка старых обновлений, чтобы не было конфликта
async def clear_updates():
    await bot.delete_webhook(drop_pending_updates=True)
    print("Webhook удален, старые обновления очищены")

asyncio.run(clear_updates())

# ===== Проверка владельца =====
def owner_only(func):
    async def wrapper(message: types.Message):
        if message.from_user.id != OWNER_ID:
            await message.reply("⛔ Эта команда доступна только главному")
            return
        await func(message)
    return wrapper

# ===== Главное меню =====
@dp.message(Command("start"))
@owner_only
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Codeforces", callback_data="cf")],
        [InlineKeyboardButton(text="Случайное число", callback_data="random")],
        [InlineKeyboardButton(text="Шутка", callback_data="joke")],
        [InlineKeyboardButton(text="Помощь", callback_data="help")]
    ])
    await message.answer(f"Привет, {message.from_user.first_name}! Это твой приватный бот.", reply_markup=kb)

# ===== Команды =====
@dp.message(Command("cf"))
@owner_only
async def cmd_cf(message: types.Message):
    rating = await get_cf_rating(CODEFORCES_HANDLE)
    await message.reply(f"💻 {CODEFORCES_HANDLE} — рейтинг: {rating}")

@dp.message(Command("random"))
@owner_only
async def cmd_random(message: types.Message):
    await message.reply(f"🎲 Случайное число: {random.randint(1,100)}")

@dp.message(Command("joke"))
@owner_only
async def cmd_joke(message: types.Message):
    await message.reply("😂 Почему программисты любят темноту? Потому что свет привлекает баги!")

@dp.message(Command("help"))
@owner_only
async def cmd_help(message: types.Message):
    await message.reply("""
Доступные команды:
/start - Главное меню
/cf - Рейтинг Codeforces
/random - Случайное число
/joke - Шутка
/help - Список команд
""")

# ===== Обработчик кнопок =====
@dp.callback_query()
async def cb_handler(query: types.CallbackQuery):
    await query.answer()
    if query.from_user.id != OWNER_ID:
        await query.message.edit_text("⛔ Эта кнопка доступна только главному")
        return

    if query.data == "cf":
        rating = await get_cf_rating(CODEFORCES_HANDLE)
        await query.message.edit_text(f"💻 {CODEFORCES_HANDLE} — рейтинг: {rating}")
    elif query.data == "random":
        await query.message.edit_text(f"🎲 Случайное число: {random.randint(1,100)}")
    elif query.data == "joke":
        await query.message.edit_text("😂 Почему программисты любят темноту? Потому что свет привлекает баги!")
    elif query.data == "help":
        await query.message.edit_text("""
/start - Главное меню
/cf - Рейтинг Codeforces
/random - Случайное число
/joke - Шутка
/help - Список команд
""")

# ===== Codeforces API =====
async def get_cf_rating(handle):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://codeforces.com/api/user.info?handles={handle}") as resp:
                data = await resp.json()
                if data["status"] == "OK":
                    user = data["result"][0]
                    return user.get("rating", "—")
                return "не найдено"
    except:
        return "ошибка"

# ===== Запуск бота =====
if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))

