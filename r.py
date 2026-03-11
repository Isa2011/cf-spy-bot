import asyncio, sqlite3, random, logging, os, aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8653073291:AAE2wrd9z9uQecOAs12qCWuinCBlY6ljf5w"
PORT = int(os.environ.get("PORT", 10000))
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect("spy.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS watching (chat_id INTEGER, handle TEXT, last_sub_id INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, tasks INTEGER DEFAULT 0, xp INTEGER DEFAULT 0, lvl INTEGER DEFAULT 1, todo TEXT DEFAULT '')")
    conn.commit()
    conn.close()

init_db()

# --- WEB SERVER (Для Render) ---
async def handle(request): return web.Response(text="Spy Bot is Active")
async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()

# --- CF SPY LOGIC ---
async def check_cf_updates():
    while True:
        try:
            conn = sqlite3.connect("spy.db")
            cur = conn.cursor()
            cur.execute("SELECT chat_id, handle, last_sub_id FROM watching")
            targets = cur.fetchall()
            async with aiohttp.ClientSession() as session:
                for chat_id, handle, last_id in targets:
                    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=1"
                    async with session.get(url, timeout=5) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data["status"] == "OK" and data["result"]:
                                s = data["result"][0]
                                if s["id"] != last_id:
                                    if s.get("verdict") == "OK":
                                        p = s["problem"]
                                        rating = p.get('rating', '???')
                                        msg = f"🔥 **{handle}** затащил задачу!\n🔹 `{p['index']}. {p['name']}`\n📊 Рейтинг: **{rating}**"
                                        await bot.send_message(chat_id, msg, parse_mode="Markdown")
                                    cur.execute("UPDATE watching SET last_sub_id = ? WHERE chat_id = ? AND handle = ?", (s["id"], chat_id, handle))
                                    conn.commit()
            conn.close()
        except: pass
        await asyncio.sleep(60)

# --- КОМАНДЫ ШПИОНАЖА ---
@dp.message(Command("cf_follow"))
async def f(m: types.Message):
    h = m.text.replace("/cf_follow", "").strip()
    if not h: return await m.answer("Укажи ник!")
    conn = sqlite3.connect("spy.db"); cur = conn.cursor()
    cur.execute("INSERT INTO watching VALUES (?, ?, 0)", (m.chat.id, h))
    conn.commit(); conn.close()
    await m.answer(f"👀 Слежу за `{h}`. Как решит — маякну!")

@dp.message(Command("cf_list"))
async def cf_l(m: types.Message):
    conn = sqlite3.connect("spy.db"); cur = conn.cursor()
    cur.execute("SELECT handle FROM watching WHERE chat_id = ?", (m.chat.id,))
    res = cur.fetchall()
    if not res: return await m.answer("Список слежки пуст.")
    await m.answer("🕵️‍♂️ **Ты следишь за:**\n" + "\n".join([f"• {r[0]}" for r in res]))

# --- КОМАНДЫ ПРОГРЕССА ---
@dp.message(Command("done"))
async def d(m: types.Message):
    task = m.text.replace("/done", "").strip() or "Задача"
    conn = sqlite3.connect("spy.db"); cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (m.from_user.id, m.from_user.full_name))
    cur.execute("UPDATE users SET tasks = tasks + 1, xp = xp + 50, lvl = (xp + 50) / 200 + 1 WHERE id = ?", (m.from_user.id,))
    conn.commit(); conn.close()
    await m.answer(f"✅ Красава! +50 XP за: {task}")

@dp.message(Command("stats"))
async def st(m: types.Message):
    conn = sqlite3.connect("spy.db"); cur = conn.cursor()
    cur.execute("SELECT tasks, xp, lvl FROM users WHERE id = ?", (m.from_user.id,))
    d = cur.fetchone()
    if not d: return await m.answer("Напиши /done для начала!")
    await m.answer(f"👤 **{m.from_user.first_name}**\n🏆 LVL: {d[2]}\n🔥 XP: {d[1]}\n🎯 Задач: {d[0]}")

# --- ТУЛЗЫ И ФАН (РЕАЛЬНЫЕ) ---
@dp.message(Command("calc"))
async def calc(m: types.Message):
    try:
        expr = m.text.replace("/calc", "").strip()
        await m.answer(f"🔢 Результат: `{eval(expr, {'__builtins__': {}})}`")
    except: await m.answer("Ошибка! Пример: `/calc 1024 / 8`")

@dp.message(Command("roll"))
async def roll(m: types.Message): await m.answer(f"🎲 Выпало: {random.randint(1, 100)}")

@dp.message(Command("joke"))
async def joke(m: types.Message):
    jokes = ["Билл Гейтс заходит в бар... а там 404.", "Почему программисты путают Хэллоуин и Рождество? Потому что 31 Oct = 25 Dec."]
    await m.answer(random.choice(jokes))

@dp.message(Command("help"))
async def h(m: types.Message):
    await m.answer("🚀 **Spy Bot 2.0**\n\n**CF:** /cf_follow, /cf_list, /cf_check\n**Stats:** /done, /stats, /top, /rank\n**Tools:** /calc, /joke, /roll, /ping, /id")

# --- ЗАПУСК ---
async def main():
    asyncio.create_task(start_web_server())
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(check_cf_updates())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
