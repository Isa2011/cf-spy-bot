import telebot
import requests
import time
import threading

TOKEN = '8653073291:AAHAszBr4peH4c4A_QpxqboW4UwN_UXZF4g'
MY_CHAT_ID = 7951275068  # Твой ID (можно узнать у бота @userinfobot)
bot = telebot.TeleBot(TOKEN)

# Список тех, за кем следим
WATCH_LIST = ['Alihan_7', 'NullPhase', 'whyy', 'matano'] 
# Тут храним ID последней решенной задачи, чтобы не спамить
last_solved_ids = {}

def check_updates():
    while True:
        for handle in WATCH_LIST:
            try:
                url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=5"
                data = requests.get(url).json()
                
                if data['status'] == 'OK':
                    for sub in data['result']:
                        if sub['verdict'] == 'OK':
                            sub_id = sub['id']
                            
                            # Если этой задачи нет в базе или она новее последней известной
                            if handle not in last_solved_ids:
                                last_solved_ids[handle] = sub_id
                                break # Просто запоминаем текущую при первом запуске
                            
                            if sub_id > last_solved_ids[handle]:
                                prob = sub['problem']
                                message = (f"🔥 {handle} решил задачу!\n"
                                           f"Задача: {prob['name']} (Рейтинг: {prob.get('rating', '???')})\n"
                                           f"Ссылка: https://codeforces.com/contest/{prob['contestId']}/problem/{prob['index']}")
                                
                                bot.send_message(MY_CHAT_ID, message)
                                last_solved_ids[handle] = sub_id
            except Exception as e:
                print(f"Ошибка проверки {handle}: {e}")
        
        time.sleep(60) # Ждем минуту перед следующей проверкой

# Запускаем проверку в отдельном потоке, чтобы бот не "зависал"
threading.Thread(target=check_updates, daemon=True).start()

print("Бот-шпион запущен!")
bot.infinity_polling()