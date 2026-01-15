import json
import os
import telebot

# Настройки из переменных окружения
TOKEN = os.environ.get("BOT_TOKEN", "8274329230:AAE6NGyu5_R_RuiYvn6GB8HFAqMcbqTpvrw")
ADMIN = int(os.environ.get("ADMIN_ID", "7620190298"))

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "/data/data.json"  # Railway сохраняет тут

def load():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Конвертируем в float на всякий случай
            for key in ['balance', 'earned', 'paid', 'rate', 'percent']:
                if key in data:
                    data[key] = float(data[key])
            return data
    except:
        return {"balance": 0.0, "earned": 0.0, "paid": 0.0, "rate": 92.5, "percent": 2.5, "transactions": []}

def save(data):
    # Создаем папку если нет
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == ADMIN:
        reply = """✅ *БОТ РАБОТАЕТ 24/7*

*КОМАНДЫ:*
➕ `+5000` - добавить 5000₽
💰 `выплата 1000` - выплатить 1000 USDT
📊 `/balance` - баланс
🔢 `/setrate 92.5` - курс
📌 `/setpercent 2.5` - процент
📈 `/stats` - статистика
👑 `/addadmin ID` - добавить админа
        """
        bot.reply_to(message, reply, parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ Нет доступа")

@bot.message_handler(func=lambda m: m.text and m.text[0] == '+')
def add_money(message):
    if message.from_user.id != ADMIN:
        return
    
    try:
        amount = float(message.text[1:].strip().replace(',', '.'))
        data = load()
        
        usdt = amount / data['rate']
        fee = usdt * (data['percent'] / 100)
        net = usdt - fee
        
        data['balance'] += net
        data['earned'] += net
        
        # Добавляем в историю
        if 'transactions' not in data:
            data['transactions'] = []
        data['transactions'].append({
            'type': 'add',
            'amount_rub': amount,
            'amount_usdt': usdt,
            'net': net,
            'time': telebot.util.quick_markup()  # timestamp
        })
        
        save(data)
        
        reply = f"""
✅ *+{amount:,.2f} RUB*
📊 Курс: {data['rate']} | %: {data['percent']}
💵 *USDT:* {usdt:.2f}
📉 *Комиссия:* {fee:.2f}
📈 *Баланс:* {data['balance']:.2f} USDT
        """
        bot.reply_to(message, reply, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

@bot.message_handler(func=lambda m: m.text and 'выплата' in m.text.lower())
def payment(message):
    if message.from_user.id != ADMIN:
        return
    
    try:
        # Ищем число в сообщении
        import re
        numbers = re.findall(r'\d+\.?\d*', message.text)
        if not numbers:
            bot.reply_to(message, "❌ Укажите сумму: выплата 500")
            return
        
        amount = float(numbers[0].replace(',', '.'))
        data = load()
        
        if amount > data['balance']:
            bot.reply_to(message, f"❌ Макс: {data['balance']:.2f} USDT")
            return
        
        data['balance'] -= amount
        data['paid'] += amount
        save(data)
        
        reply = f"""
💸 *Выплата:* {amount:.2f} USDT
📊 *Остаток:* {data['balance']:.2f} USDT
💰 *Всего выплачено:* {data['paid']:.2f} USDT
        """
        bot.reply_to(message, reply, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['balance'])
def balance_cmd(message):
    if message.from_user.id != ADMIN:
        return
    
    data = load()
    reply = f"""
💰 *Баланс:* {data['balance']:.2f} USDT
📈 *Начислено:* {data['earned']:.2f} USDT
📉 *Выплачено:* {data['paid']:.2f} USDT
🔢 *Курс:* {data['rate']} RUB/USDT
📌 *Процент:* {data['percent']}%
    """
    bot.reply_to(message, reply, parse_mode='Markdown')

@bot.message_handler(commands=['setrate', 'setpercent', 'addadmin', 'stats'])
def other_commands(message):
    if message.from_user.id != ADMIN:
        return
    
    cmd = message.text.split()[0]
    
    if cmd == '/setrate':
        try:
            rate = float(message.text.split()[1])
            data = load()
            data['rate'] = rate
            save(data)
            bot.reply_to(message, f"✅ Курс: 1 USDT = {rate} RUB")
        except:
            bot.reply_to(message, "❌ /setrate 92.5")
    
    elif cmd == '/setpercent':
        try:
            percent = float(message.text.split()[1])
            data = load()
            data['percent'] = percent
            save(data)
            bot.reply_to(message, f"✅ Процент: {percent}%")
        except:
            bot.reply_to(message, "❌ /setpercent 2.5")
    
    elif cmd == '/stats':
        data = load()
        transactions = data.get('transactions', [])
        reply = f"""
📊 *Статистика*
Транзакций: {len(transactions)}
Баланс: {data['balance']:.2f} USDT
Курс: {data['rate']} | %: {data['percent']}
        """
        bot.reply_to(message, reply, parse_mode='Markdown')

print(f"👑 Админ ID: {ADMIN}")
bot.infinity_polling(timeout=60, long_polling_timeout=5)
