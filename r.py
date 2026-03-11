import logging
import random
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8653073291:AAG6jr04iA3i6-_3VXsHjSgXoipZtSC88fM"
OWNER_ID = 7951275068

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== Проверка владельца =====
async def check_owner(message: types.Message | types.CallbackQuery):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        if isinstance(message, types.Message):
            await message.reply("⛔ Эта команда доступна только главному")
        else:
            await message.message.edit_text("⛔ Эта кнопка доступна только главному")
        return False
    return True

# ===== Хранилище пользователей Codeforces =====
tracked_users = []  # список handle

# ===== Главное меню =====
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not await check_owner(message):
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Codeforces", callback_data="cf")],
        [InlineKeyboardButton(text="Случайное число", callback_data="random")],
        [InlineKeyboardButton(text="Шутка", callback_data="joke")],
        [InlineKeyboardButton(text="Помощь", callback_data="help")]
    ])
    await message.answer(f"Привет, {message.from_user.first_name}! Это твой приватный бот.", reply_markup=kb)

# ===== Команды =====
@dp.message(Command("cf"))
async def cmd_cf(message: types.Message):
    if not await check_owner(message):
        return
    rating = await get_cf_rating("whyy")
    await message.reply(f"💻 whyy — рейтинг: {rating}")

@dp.message(Command("random"))
async def cmd_random(message: types.Message):
    if not await check_owner(message):
        return
    await message.reply(f"🎲 Случайное число: {random.randint(1,100)}")

@dp.message(Command("joke"))
async def cmd_joke(message: types.Message):
    if not await check_owner(message):
        return
    await message.reply("😂 Почему программисты любят темноту? Потому что свет привлекает баги!")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    if not await check_owner(message):
        return
    await message.reply("""
Доступные команды:
/start - Главное меню
/cf - Рейтинг Codeforces
/random - Случайное число
/joke - Шутка
/help - Список команд
/add <handle> - Добавить пользователя Codeforces
/list - Показать список отслеживаемых пользователей
""")

# ===== Новые команды: add и list =====
@dp.message(Command("add"))
async def cmd_add(message: types.Message):
    if not await check_owner(message):
        return
    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        await message.reply("❌ Использование: /add <handle>")
        return
    handle = args[1].strip()
    if handle in tracked_users:
        await message.reply(f"⚠ {handle} уже добавлен")
        return
    # Проверяем, существует ли такой handle
    rating = await get_cf_rating(handle)
    if rating == "не найдено" or rating == "ошибка":
        await message.reply(f"❌ Пользователь {handle} не найден на Codeforces")
        return
    tracked_users.append(handle)
    await message.reply(f"✅ {handle} успешно добавлен с рейтингом {rating}")

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    if not await check_owner(message):
        return
    if not tracked_users:
        await message.reply("📋 Список пуст")
        return
    reply_text = "📋 Отслеживаемые пользователи:\n"
    for handle in tracked_users:
        rating = await get_cf_rating(handle)
        reply_text += f"💻 {handle} — рейтинг: {rating}\n"
    await message.reply(reply_text)

# ===== Обработчик кнопок =====
@dp.callback_query()
async def cb_handler(query: types.CallbackQuery):
    if not await check_owner(query):
        return
    await query.answer()
    if query.data == "cf":
        rating = await get_cf_rating("whyy")
        await query.message.edit_text(f"💻 whyy — рейтинг: {rating}")
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
/add <handle> - Добавить пользователя Codeforces
/list - Показать список отслеживаемых пользователей
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

    async def main():
        # очистка старых обновлений
        await bot.delete_webhook(drop_pending_updates=True)
        print("Webhook удален, старые обновления очищены")
        await dp.start_polling(bot)

    asyncio.run(main())
