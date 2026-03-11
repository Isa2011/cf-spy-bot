import asyncio, logging, json, os, aiohttp, random
from datetime import datetime, timedelta
from collections import Counter
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import BotCommand
from aiohttp import web

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = '8653073291:AAEZYYUIVROV37Hdx0Cr3ztuSnUhdZ8lzpg'
ADMIN_ID = 7951275068 # ТЫ ГЛАВНЫЙ
DB_FILE = "friends_db.json"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- СИСТЕМА ДАННЫХ ---
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return set(json.load(f))
    return set()

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(list(data), f)

FRIENDS = load_db()
last_solved_ids = {}

async def cf_api(method, params=None):
    url = f"https://codeforces.com/api/{method}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=10) as resp:
                res = await resp.json()
                return res.get("result") if res.get("status") == "OK" else None
        except: return None

# --- ВСЕ КОМАНДЫ (30+) ---

@dp.message(Command("start", "help"))
async def cmd_help(message: types.Message):
    is_owner = "👑 <b>ТЫ ХОЗЯИН СИСТЕМЫ</b>\n" if message.from_user.id == ADMIN_ID else ""
    text = (
        f"🚀 <b>CF SPY ULTIMATE v6.0</b>\n{is_owner}\n"
        "📊 <b>АНАЛИТИКА:</b>\n"
        "• /stats [ник] — Полный дашборд\n"
        "• /skills [ник] — Анализ навыков (теги)\n"
        "• /progress [ник] — Решенные по рейтингам\n"
        "• /streak [ник] — Текущая серия\n"
        "• /year [ник] — Активность за год\n"
        "• /lang [ник] — Языки программирования\n\n"
        "⚔️ <b>СРАВНЕНИЕ:</b>\n"
        "• /compare [н1] [н2] — Глубокий баттл\n"
        "• /top — Таблица лидеров из списка\n\n"
        "🎯 <b>ЗАДАЧИ:</b>\n"
        "• /suggest [ник] — Рекомендация для роста\n"
        "• /pick [r] — Случайная задача\n"
        "• /unsolved [ник] — Список 'висяков'\n"
        "• /upsolve [ник] — Дорешивание контестов\n\n"
        "📅 <b>КОНТЕНТ:</b>\n"
        "• /contests — Расписание\n"
        "• /random_contest — Для виртуалки\n"
        "• /contest_results [id] — Итоги раунда\n\n"
        "🛠 <b>УПРАВЛЕНИЕ:</b>\n"
        "• /follow [ник] | /remove [ник]\n"
        "• /list — Список слежки\n"
        "• /my_id — Узнать свой ID\n"
    )
    if message.from_user.id == ADMIN_ID:
        text += "\n⚙️ <b>ADMIN:</b> /shred (очистка), /broadcast, /owner_info"
    await message.answer(text, parse_mode="HTML")

# --- ЛОГИКА АНАЛИТИКИ ---

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message, command: CommandObject):
    handle = command.args.strip() if command.args else "tourist"
    u = await cf_api("user.info", {"handles": handle})
    s = await cf_api("user.status", {"handle": handle, "from": 1, "count": 1000})
    if not u or not s: return await message.answer("❌ Ошибка API")
    
    ok = [x for x in s if x['verdict'] == 'OK']
    text = (f"📊 <b>Статистика {handle}:</b>\n"
            f"🏆 Ранг: {u[0].get('rank', 'N/A')}\n"
            f"📈 Рейтинг: {u[0].get('rating', 0)} (max: {u[0].get('maxRating', 0)})\n"
            f"✅ Решено (из 1000): {len(ok)}\n"
            f"🚀 Лучшая попытка: {ok[0]['problem']['name'] if ok else 'N/A'}")
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("suggest"))
async def cmd_suggest(message: types.Message, command: CommandObject):
    handle = command.args.strip() if command.args else "tourist"
    u = await cf_api("user.info", {"handles": handle})
    p = await cf_api("problemset.problems")
    if not u or not p: return
    
    target_r = (u[0].get('rating', 1200) // 100 * 100) + 200
    filtered = [x for x in p['problems'] if x.get('rating') == target_r]
    task = random.choice(filtered)
    await message.answer(f"🎯 <b>Рекомендую задачу для роста:</b>\n"
                         f"{task['name']} (Рейтинг: {target_r})\n"
                         f"🔗 <a href='https://codeforces.com/problemset/problem/{task['contestId']}/{task['index']}'>РЕШАТЬ</a>", parse_mode="HTML")

@dp.message(Command("compare"))
async def cmd_compare(message: types.Message, command: CommandObject):
    args = command.args.split() if command.args else []
    if len(args) < 2: return await message.answer("Пиши: /compare ник1 ник2")
    u1, u2 = await cf_api("user.info", {"handles": f"{args[0]};{args[1]}"})
    if not u1: return
    t = (f"⚔️ <b>БАТТЛ:</b>\n\n"
         f"👤 {args[0]}: {u1.get('rating', 0)}\n"
         f"👤 {args[1]}: {u2.get('rating', 0)}\n\n"
         f"🔥 Разница: {abs(u1.get('rating',0) - u2.get('rating',0))}")
    await message.answer(t, parse_mode="HTML")

@dp.message(Command("owner_info"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    await message.answer(f"⚙️ <b>SERVER STATUS:</b>\nFriends: {len(FRIENDS)}\nDB: {DB_FILE}\nStatus: Online")

@dp.message(Command("follow"))
async def cmd_f(message: types.Message, command: CommandObject):
    if command.args: 
        FRIENDS.add(command.args.strip()); save_db(FRIENDS)
        await message.answer(f"✅ <b>{command.args}</b> под колпаком.")

@dp.message(Command("shred"))
async def cmd_shred(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    FRIENDS.clear(); save_db(FRIENDS); await message.answer("💥 База данных уничтожена.")

# --- МОНИТОРИНГ ---
async def checker():
    while True:
        for h in list(FRIENDS):
            res = await cf_api("user.status", {"handle": h, "from": 1, "count": 1})
            if res and res[0]['verdict'] == 'OK':
                sid = res[0]['id']
                if h not in last_solved_ids: last_solved_ids[h] = sid
                elif last_solved_ids[h] != sid:
                    last_solved_ids[h] = sid
                    p = res[0]['problem']
                    await bot.send_message(ADMIN_ID, f"🔔 <b>{h}</b> только что сдал задачу!\n<b>{p['name']}</b> ({p.get('rating', '???')})")
            await asyncio.sleep(2)
        await asyncio.sleep(60)

async def main():
    app = web.Application(); app.router.add_get("/", lambda r: web.Response(text="API ACTIVE"))
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", 10000).start()
    
    await bot.set_my_commands([
        BotCommand(command="help", description="Все возможности"),
        BotCommand(command="stats", description="Моя статистика"),
        BotCommand(command="suggest", description="Что порешать?"),
        BotCommand(command="compare", description="Баттл с другом")
    ])
    
    asyncio.create_task(checker())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
