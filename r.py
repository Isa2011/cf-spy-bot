import asyncio
import random
import logging
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.bot import DefaultBotProperties

# ---------------- Настройки ----------------
TOKEN = "8771638954:AAG9mrksptIJKh-62ltsIVp-UF1E8GTqswA"
OWNER_ID = 7951275068
CHAT_ID = -4993544380
MY_HANDLE = "whyy"
CHECK_INTERVAL = 60

# Webhook
WEBHOOK_HOST = "https://your-app.onrender.com"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# ---------------- Локальные переменные ----------------
last_submissions = {}
session: aiohttp.ClientSession = None

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Предложить задачу")],
        [KeyboardButton(text="Моя статистика")],
        [KeyboardButton(text="Топ друзей")],
        [KeyboardButton(text="Рейтинг")]
    ],
    resize_keyboard=True
)

# ---------------- Бот ----------------
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# ---------------- API ----------------
async def get_user_info(handle):
    async with session.get(f"https://codeforces.com/api/user.info?handles={handle}") as r:
        return (await r.json())["result"][0]

async def get_user_submissions(handle):
    async with session.get(f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=50") as r:
        return (await r.json())["result"]

async def get_problems():
    async with session.get("https://codeforces.com/api/problemset.problems") as r:
        return (await r.json())["result"]

async def get_contests():
    async with session.get("https://codeforces.com/api/contest.list") as r:
        return (await r.json())["result"]

async def get_friends():
    async with session.get(f"https://codeforces.com/api/user.friends?handle={MY_HANDLE}") as r:
        return (await r.json())["result"]

# ---------------- Мониторинг ----------------
async def monitor_friends():
    await bot.wait_until_ready()
    while True:
        try:
            friends = await get_friends()
            for handle in friends:
                subs = await get_user_submissions(handle)
                if not subs:
                    continue
                if handle not in last_submissions:
                    last_submissions[handle] = subs[0]["id"]
                    continue
                for s in subs:
                    if s["id"] == last_submissions[handle]:
                        break
                    if s["verdict"] == "OK":
                        p = s["problem"]
                        link = f"https://codeforces.com/problemset/problem/{p['contestId']}/{p['index']}"
                        msg = f"Пользователь {handle} только что решил задачу:\n\n<a href='{link}'>{p['name']}</a>\nРейтинг задачи: {p.get('rating','?')}"
                        await bot.send_message(OWNER_ID, msg)
                        await bot.send_message(CHAT_ID, msg)
                last_submissions[handle] = subs[0]["id"]
        except Exception as e:
            print("Ошибка мониторинга друзей:", e)
        await asyncio.sleep(CHECK_INTERVAL)

# ---------------- Suggest ----------------
async def suggest_problem():
    user = await get_user_info(MY_HANDLE)
    rating = user.get("rating", 1200)
    data = await get_problems()
    problems = data["problems"]
    subs = await get_user_submissions(MY_HANDLE)
    solved = {(s["problem"]["contestId"], s["problem"]["index"]) for s in subs if s["verdict"]=="OK"}
    candidates = [p for p in problems if "rating" in p and rating+100 <= p["rating"] <= 2500 and (p["contestId"], p["index"]) not in solved]
    if not candidates:
        return "Не найдено задач"
    p = random.choice(candidates)
    link = f"https://codeforces.com/problemset/problem/{p['contestId']}/{p['index']}"
    return f"Попробуй решить задачу:\n\n<a href='{link}'>{p['name']}</a>\nРейтинг: {p['rating']}"

# ---------------- Команды ----------------
@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("Бот Codeforces запущен!", reply_markup=keyboard)

@dp.message(Command("help"))
async def help_cmd(msg: types.Message):
    text = "/suggest — предложить задачу\n/stats — статистика\n/top — топ друзей\n/solved — решено задач\n/rating — рейтинг\n/contest — контесты"
    await msg.answer(text)

@dp.message(Command("suggest"))
async def suggest(msg: types.Message):
    await msg.answer(await suggest_problem())

# ---------------- Keep Alive ----------------
async def handle(request):
    return web.Response(text="Bot alive")

# ---------------- Webhook ----------------
async def on_startup():
    global session
    session = aiohttp.ClientSession()
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(monitor_friends())

async def on_shutdown():
    await bot.delete_webhook()
    await bot.session.close()
    await session.close()

app = web.Application()
app.router.add_post(WEBHOOK_PATH, bot.webhook_handler)
app.router.add_get('/', handle)

# ---------------- Запуск ----------------
if __name__ == "__main__":
    web.run_app(app, host='0.0.0.0', port=8080, shutdown_timeout=5)
    asyncio.run(on_startup())
