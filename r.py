import asyncio
import logging
import random
import aiohttp
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = "8653073291:AAG6jr04iA3i6-_3VXsHjSgXoipZtSC88fM"
OWNER_ID = 7951275068

bot = Bot(TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# ===== файлы =====

USERS_FILE = "users.json"
XP_FILE = "xp.json"

# ===== загрузка =====

def load(file):
    try:
        with open(file,"r") as f:
            return json.load(f)
    except:
        return {}

def save(file,data):
    with open(file,"w") as f:
        json.dump(data,f)

tracked = load(USERS_FILE)
xp = load(XP_FILE)

last_submission = {}

# ===== уровни =====

def level(points):
    return points // 100

# ===== мотивация =====

motivation = [
"🔥 Ты можешь стать сильнее!",
"⚡ Реши ещё одну задачу!",
"🚀 Не останавливайся!",
"👑 Будущий Grandmaster!",
"💪 Тренируйся каждый день!"
]

# ===== Codeforces API =====

async def cf_user(handle):

    async with aiohttp.ClientSession() as s:

        url=f"https://codeforces.com/api/user.info?handles={handle}"

        async with s.get(url) as r:

            data=await r.json()

            if data["status"]!="OK":
                return None

            return data["result"][0]

# ===== задачи =====

async def random_problem():

    async with aiohttp.ClientSession() as s:

        url="https://codeforces.com/api/problemset.problems"

        async with s.get(url) as r:

            data=await r.json()

            problems=data["result"]["problems"]

            p=random.choice(problems)

            return f"https://codeforces.com/problemset/problem/{p['contestId']}/{p['index']}"

# ===== добавление пользователя =====

@dp.message(Command("add"))
async def add(message:types.Message):

    args=message.text.split()

    if len(args)<2:
        await message.answer("/add handle")
        return

    handle=args[1]

    tracked[handle]=True
    save(USERS_FILE,tracked)

    await message.answer(f"✅ {handle} добавлен")

# ===== удалить =====

@dp.message(Command("remove"))
async def remove(message:types.Message):

    args=message.text.split()

    if len(args)<2:
        return

    handle=args[1]

    if handle in tracked:
        del tracked[handle]
        save(USERS_FILE,tracked)

    await message.answer("❌ удален")

# ===== список =====

@dp.message(Command("list"))
async def list_users(message:types.Message):

    if not tracked:
        await message.answer("пусто")
        return

    text="👀 Отслеживаемые\n\n"

    for u in tracked:
        text+=f"• {u}\n"

    await message.answer(text)

# ===== рейтинг =====

@dp.message(Command("rating"))
async def rating(message:types.Message):

    args=message.text.split()

    if len(args)<2:
        return

    handle=args[1]

    u=await cf_user(handle)

    if not u:
        await message.answer("не найден")
        return

    await message.answer(
f"""
👤 {handle}

📈 rating: {u.get("rating",0)}
🏆 rank: {u.get("rank","")}
"""
)

# ===== случайная задача =====

@dp.message(Command("problem"))
async def problem(message:types.Message):

    p=await random_problem()

    await message.answer(
f"""
🧠 Попробуй решить:

{p}

🔥 {random.choice(motivation)}
"""
)

# ===== XP =====

@dp.message(Command("xp"))
async def myxp(message:types.Message):

    uid=str(message.from_user.id)

    points=xp.get(uid,0)

    await message.answer(
f"""
🎮 XP: {points}

🏆 уровень: {level(points)}
"""
)

# ===== ежедневная тренировка =====

@dp.message(Command("daily"))
async def daily(message:types.Message):

    await message.answer(
"""
🔥 Сегодня:

реши 3 задачи
изучай DP
прочитай редакцию

🚀 ты сможешь!
"""
)

# ===== мотивация =====

@dp.message(Command("motivation"))
async def motiv(message:types.Message):

    await message.answer(random.choice(motivation))

# ===== дуэль =====

@dp.message(Command("duel"))
async def duel(message:types.Message):

    args=message.text.split()

    if len(args)<2:
        return

    enemy=args[1]

    p=await random_problem()

    await message.answer(
f"""
⚔ DUEL

Ты vs {enemy}

задача:

{p}

кто решит первым?
"""
)

# ===== топ XP =====

@dp.message(Command("top"))
async def top(message:types.Message):

    ranking=sorted(xp.items(),key=lambda x:-x[1])

    text="🏆 TOP\n\n"

    for i,(u,p) in enumerate(ranking[:10],1):

        text+=f"{i}. {u} — {p}\n"

    await message.answer(text)

# ===== help =====

@dp.message(Command("help"))
async def help(message:types.Message):

    await message.answer(
"""
📚 команды

/add
/remove
/list
/rating
/problem
/xp
/top
/daily
/motivation
/duel
"""
)

# ===== старт =====

@dp.message(Command("start"))
async def start(message:types.Message):

    await message.answer(
"""
🚀 Codeforces Spy Bot

/help
"""
)

# ===== слежка за решениями =====

async def spy():

    while True:

        try:

            async with aiohttp.ClientSession() as s:

                for u in tracked:

                    url=f"https://codeforces.com/api/user.status?handle={u}&from=1&count=1"

                    async with s.get(url) as r:

                        data=await r.json()

                        if data["status"]!="OK":
                            continue

                        sub=data["result"][0]["id"]

                        if u not in last_submission:

                            last_submission[u]=sub

                        elif last_submission[u]!=sub:

                            last_submission[u]=sub

                            await bot.send_message(
OWNER_ID,
f"""
🚨 ALERT

😱 {u} решил новую задачу!

🔥 решай быстрее!
"""
)

        except Exception as e:

            print(e)

        await asyncio.sleep(60)

# ===== main =====

async def main():

    await bot.delete_webhook(drop_pending_updates=True)

    asyncio.create_task(spy())

    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())
