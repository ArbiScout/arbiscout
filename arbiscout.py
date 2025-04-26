# ArbiScout PRO v2 — by @tvoibro

import telebot
from telebot import types
import requests
import json
import os

# === ВСТАВ СВОЇ ТОКЕНИ ТУТ ===
TELEGRAM_TOKEN = "8068344858:AAFgpujoX7h3x9ut9EAdsgvZgdrkQqCRK3Y"
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


bot = telebot.TeleBot(TELEGRAM_TOKEN)

# === СТВОРЮЄМО ФАЙЛ ДЛЯ ЗБЕРЕЖЕННЯ КОРИСТУВАЧІВ ===
USERS_FILE = "users.json"
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

USERS = load_users()

# === ID адміна ===
ADMIN_ID = 569820502  # заміни на свій Telegram ID

# === Старт бота ===
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = str(message.chat.id)
    if chat_id not in USERS:
        USERS[chat_id] = {
            "name": message.from_user.first_name,
            "pro": False,
            "cards": [],
            "balance": {"UAH": 0, "USDT": 0}
        }
        save_users(USERS)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📈 Зв'язка", "🤖 Питання по арбітражу")
    markup.add("💰 Баланс", "💳 Картки")
    markup.add("👤 Профіль", "💎 Купити PRO")
    if message.from_user.id == ADMIN_ID:
        markup.add("🛠 Адмінка")

    bot.send_message(message.chat.id, f"Привіт, {message.from_user.first_name}!\nЯ — ArbiScout. Обери дію:", reply_markup=markup)
@bot.message_handler(func=lambda m: m.text == "👤 Профіль")
def profile(message):
    chat_id = str(message.chat.id)
    user = USERS.get(chat_id, {})
    text = f"Ім’я: {user.get('name')}\nPRO: {'✅' if user.get('pro') else '❌'}\nКарток: {len(user.get('cards', []))}"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "💰 Баланс")
def balance(message):
    chat_id = str(message.chat.id)
    user = USERS.get(chat_id, {})
    bal = user.get("balance", {})
    bot.send_message(message.chat.id, f"Баланс:\nUAH: {bal.get('UAH')} ₴\nUSDT: {bal.get('USDT')} $")

@bot.message_handler(func=lambda m: m.text == "💳 Картки")
def cards(message):
    chat_id = str(message.chat.id)
    user = USERS.get(chat_id, {})
    cards = user.get("cards", [])

    if not cards:
        bot.send_message(message.chat.id, "У тебе ще немає доданих карток.")
    else:
        card_list = "\n".join(f"• {card}" for card in cards)
        bot.send_message(message.chat.id, f"Твої картки:\n{card_list}")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Додати картку", "↩️ Назад")
    bot.send_message(message.chat.id, "Що хочеш зробити?", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "➕ Додати картку")
def add_card(message):
    bot.send_message(message.chat.id, "Введи номер картки:")
    bot.register_next_step_handler(message, save_card)

def save_card(message):
    card = message.text
    chat_id = str(message.chat.id)
    USERS[chat_id]["cards"].append(card)
    save_users(USERS)
    bot.send_message(message.chat.id, "Картку збережено!")
def ask_gpt(message_text):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": message_text}],
        "temperature": 0.7
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers, json=data
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return "⚠️ Помилка з боку AI. Спробуй пізніше."

@bot.message_handler(func=lambda m: m.text == "🤖 Питання по арбітражу")
def ask_ai(message):
    bot.send_message(message.chat.id, "Напиши своє питання:")
    bot.register_next_step_handler(message, handle_ai)

def handle_ai(message):
    bot.send_message(message.chat.id, "Думаю...")
    answer = ask_gpt(message.text)
    bot.send_message(message.chat.id, answer)
@bot.message_handler(func=lambda m: m.text == "💎 Купити PRO")
def buy_pro(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    pay_url = "https://www.liqpay.ua/api/checkout"  # заміни на свою оплату
    markup.add(types.InlineKeyboardButton("Оплатити 99 грн", url=pay_url))
    bot.send_message(chat_id, "Отримай повний доступ до ArbiScout!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🛠 Адмінка")
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    total_users = len(USERS)
    total_pro = sum(1 for u in USERS.values() if u.get("pro"))
    bot.send_message(message.chat.id, f"Користувачів: {total_users}\nPRO: {total_pro}")

@bot.message_handler(func=lambda m: m.text == "↩️ Назад")
def back(message):
    return start(message)

import os
import flask
from flask import request

WEBHOOK_URL = 'https://arbiscout.onrender.com'  # встав свою ссилку сюди

app = flask.Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Invalid Content-Type', 403

if __name__ == "__main__":
    PORT = int(os.environ.get('PORT', 5000))  # динамічний порт від Render
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)

