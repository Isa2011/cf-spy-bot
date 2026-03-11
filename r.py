import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
import aiohttp

# ===== Настройки =====
TOKEN = "8653073291:AAG6jr04iA3i6-_3VXsHjSgXoipZtSC88fM"
MAIN_USER = "@kryyx7"  # твой ник в Telegram
CF_HANDLE = "whyy"  # твой Codeforces ник
# =====================

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== Меню =====
main_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Мой CF профиль", callback_data="cf_profile")],
        [InlineKeyboardButton(text="Топ команд", callback_data="top")],
        [InlineKeyboardButton(text="Вызов", callback_data="challenge")],
        [InlineKeyboardButton(text="Эхо", callback_data="echo")],
    ]
)

# ===== Проверка главного =====
def is_main_user(message: Message):
    return message.from_user.username == MAIN_USER

# ===== /start =====
@dp.message(Command(commands=["start"]))
async def start(message: Message):
    if not is_main_user(message):
        await message.reply("⛔ Эта команда доступна только главному")
        return
    await message.reply(f"✅ Привет, {MAIN_USER}! Вот твое меню:", reply_markup=main_menu)

# ===== Обработка кнопок меню =====
@dp.callback_query()
async def menu_handler(query: types.CallbackQuery):
    user = query.from_user
    if user.username != MAIN_USER:
        await query.answer("⛔ Эта команда только для главного!", show_alert=True)
        return

    data = query.data

    if data == "cf_profile":
        cf_data = await get_cf_info(CF_HANDLE)
        await query.message.answer(cf_data)
    elif data == "top":
        await query.message.answer("🏆 Топ команды: только для главного!")
    elif data == "challenge":
        await query.message.answer("⚡ Вызов принят! Готов к новым подвигам!")
    elif data == "echo":
        await query.message.answer("Используй команду /echo <текст> чтобы повторить текст")
    await query.answer()

# ===== /echo =====
@dp.message(Command(commands=["echo"]))
async def echo(message: Message):
    if not is_main_user(message):
        await message.reply("⛔ Только главный может использовать эту команду!")
        return
    text = message.text.replace("/echo", "").strip()
    if not text:
        await message.reply("❗ Используй: /echo <текст>")
        return
    await message.reply(f"📢 {text}")

# ===== Codeforces отслежка =====
async def get_cf_info(handle: str) -> str:
    url = f"https://codeforces.com/api/user.info?handles={handle}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            if data["status"] != "OK":
                return "❌ Ошибка при получении данных CF"
            user = data["result"][0]
            info = f"👤 {user['handle']}\n💎 Рейтинг: {user.get('rating', '—')}\n🏅 Ранг: {user.get('rank', '—')}"
            return info

# ===== Дополнительные команды (пример) =====
@dp.message(Command(commands=["motivate"]))
async def motivate(message: Message):
    if not is_main_user(message):
        await message.reply("❌ Только главному!")
        return
    await message.reply("💪 Ты лучший! Продолжай решать задачи на Codeforces!")

@dp.message(Command(commands=["fun"]))
async def fun(message: Message):
    if not is_main_user(message):
        await message.reply("😂 Только главному доступно веселье!")
        return
    await message.reply("🎉 Главное — кайфовать от каждого контеста!")

# ===== Запуск бота =====
async def main():
    print("Бот стартовал...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
