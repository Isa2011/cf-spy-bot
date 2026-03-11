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

# ===== мотивация =====

motivation = [
"🔥 Ты станешь легендой Codeforces",
"⚡ Сегодня ты станешь сильнее",
"🚀 Никогда не сдавайся",
"👑 Grandmaster начинается с одной задачи",
"💪 Решай ещё одну!"
]

# ===== троллинг =====

taunt = [
"😱 О НЕТ! Он решил задачу!",
"🚨 Срочно решай быстрее!",
"💀 Ты отстаешь...",
"🔥 Он становится сильнее!",
"👀 Похоже тебе пора тренироваться"
]

# ===== уровни =====

def level(points):
    return points // 100

# ===== Codeforces API =====

async def cf_user(handle):

    async with aiohttp.ClientSession() as s:

        url=f"https://codeforces.com/api/user.info?handles={handle}"

        async with s.get(url) as r:

            data=await r.json()

            if data["status"]!="OK":
                return None

            return data["result"][0]

# ===== random problem =====

async def random_problem():

    async with aiohttp.ClientSession() as s:

        url="https://codeforces.com/api/problemset.problems"

        async with s.get(url) as r:

            data=await r.json()

            problems=data["result"]["problems"]

            p=random.choice(problems)

            return f"https://codeforces.com/problemset/problem/{p['contestId']}/{p['index']}"

# ===== start =====

@dp.message(Command("start"))
async def start(message:types.Message):

    await message.answer(
"""
🚀 *Codeforces Spy Bot*

💻 следит за соперниками  
⚔ помогает тренироваться  
🔥 мотивирует

/help
""",
parse_mode="Markdown"
)

# ===== help =====

@dp.message(Command("help"))
async def help(message:types.Message):

    await message.answer(
"""
📚 КОМАНДЫ

👀 слежка
/add
/remove
/list

📊 Codeforces
/rating
/info
/history

🧠 задачи
/problem
/easy
/medium
/hard

🎮 игры
/coin
/dice

🏆 система
/xp
/top
/level

⚔ дуэли
/duel

🔥 мотивация
/motivation
/daily
/goal
"""
)

# ===== add =====

@dp.message(Command("add"))
async def add(message:types.Message):

    args=message.text.split()

    if len(args)<2:
        await message.answer("используй /add handle")
        return

    handle=args[1]

    tracked[handle]=True
    save(USERS_FILE,tracked)

    await message.answer(f"✅ теперь я слежу за {handle}")

# ===== remove =====

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

# ===== list =====

@dp.message(Command("list"))
async def list_users(message:types.Message):

    if not tracked:
        await message.answer("список пуст")
        return

    text="👀 отслеживаемые\n\n"

    for u in tracked:
        text+=f"• {u}\n"

    await message.answer(text)

# ===== rating =====

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

📈 рейтинг: {u.get("rating",0)}
🏆 ранг: {u.get("rank","")}

🔥 {random.choice(motivation)}
"""
)

# ===== info =====

@dp.message(Command("info"))
async def info(message:types.Message):

    args=message.text.split()

    if len(args)<2:
        return

    handle=args[1]

    u=await cf_user(handle)

    if not u:
        return

    await message.answer(
f"""
👤 {handle}

🏆 rank: {u.get("rank")}
📈 rating: {u.get("rating")}
⭐ max rating: {u.get("maxRating")}
"""
)

# ===== задачи =====

@dp.message(Command("problem"))
async def problem(message:types.Message):

    p=await random_problem()

    await message.answer(
f"""
🧠 задача

{p}

🔥 {random.choice(motivation)}
"""
)

@dp.message(Command("easy"))
async def easy(message:types.Message):

    await message.answer("🟢 easy задача\n"+await random_problem())

@dp.message(Command("medium"))
async def medium(message:types.Message):

    await message.answer("🟡 medium задача\n"+await random_problem())

@dp.message(Command("hard"))
async def hard(message:types.Message):

    await message.answer("🔴 hard задача\n"+await random_problem())

# ===== XP =====

@dp.message(Command("xp"))
async def xp_cmd(message:types.Message):

    uid=str(message.from_user.id)

    points=xp.get(uid,0)

    await message.answer(
f"""
🎮 XP: {points}

🏆 уровень: {level(points)}
"""
)

# ===== top =====

@dp.message(Command("top"))
async def top(message:types.Message):

    ranking=sorted(xp.items(),key=lambda x:-x[1])

    text="🏆 TOP\n\n"

    for i,(u,p) in enumerate(ranking[:10],1):

        text+=f"{i}. {u} — {p}\n"

    await message.answer(text)

# ===== игры =====

@dp.message(Command("coin"))
async def coin(message:types.Message):

    r=random.choice(["орел","решка"])

    await message.answer(f"🪙 {r}")

@dp.message(Command("dice"))
async def dice(message:types.Message):

    await message.answer(f"🎲 {random.randint(1,6)}")

# ===== мотивация =====

@dp.message(Command("motivation"))
async def motiv(message:types.Message):

    await message.answer(random.choice(motivation))

# ===== daily =====

@dp.message(Command("daily"))
async def daily(message:types.Message):

    await message.answer(
"""
🔥 сегодня

реши 3 задачи
прочитай editorial
изучи новую тему

🚀 вперед!
"""
)

# ===== duel =====

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

ты vs {enemy}

{p}

кто решит быстрее?
"""
)

# ===== spy =====

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

                        submission = data["result"][0]

                        sub = submission["id"]
                        
                        problem = submission["problem"]
                        
                        contest = problem["contestId"]
                        index = problem["index"]
                        
                        name = problem["name"]
                        rating = problem.get("rating","?")
                        
                        link = f"https://codeforces.com/contest/{contest}/problem/{index}"

                        if u not in last_submission:

                            last_submission[u]=sub

                        elif last_submission[u]!=sub:

                            last_submission[u]=sub

                            await bot.send_message(
OWNER_ID,
f"""
🚨 ALERT

{random.choice(taunt)}

👤 {u} решил новую задачу!

🔥 быстрее решай!
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

