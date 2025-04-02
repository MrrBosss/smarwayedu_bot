import telebot
from telebot import types
import json
import re
from flask import Flask, request
import os

# Initialize Flask app
server = Flask(__name__)

# Replace with your bot token
bot = telebot.TeleBot("7330127698:AAFNVUPAXpw80JAP7qLNjpYNTQdMD497pI8")

# File to store user data
USER_DATA_FILE = 'registered_users.json'

# Load existing user data or initialize an empty list
try:
    with open(USER_DATA_FILE, 'r') as f:
        registered_users = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    registered_users = []

# Dictionary to store user state and data during registration
user_states = {}

# Step 1: Welcome message with buttons
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn1 = types.KeyboardButton("Consulting")
    btn2 = types.KeyboardButton("Til kursi")
    markup.add(btn1, btn2)

    bot.send_message(message.chat.id, 
                     "Assalomu Alaykum! SMART WAY EDU community ga xush kelibsiz! Biz sizga quyidagi xizmatlarni taklif qilamiz:", 
                     reply_markup=markup)
    user_states[message.chat.id] = {'step': 'choose_service'}

# Handle user input for service selection
@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'choose_service')
def handle_service_choice(message):
    chat_id = message.chat.id
    text = message.text

    if text in ["Consulting", "Til kursi"]:
        user_states[chat_id]['service'] = text
        bot.send_message(chat_id, f"Siz {text} xizmatini tanladingiz! Ajoyib!")
        ask_name(chat_id)
    else:
        bot.send_message(chat_id, "Iltimos tugmalardan birini tanlang!")

# Step 2: Ask for name
def ask_name(chat_id):
    bot.send_message(chat_id, "Iltimos, ismingizni kiriting (masalan: Abduvali Abdumuratov):")
    user_states[chat_id]['step'] = 'get_name'

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'get_name')
def handle_name(message):
    chat_id = message.chat.id
    name = message.text.strip()

    if re.match(r'^[a-zA-Z\s]+$', name) and len(name.split()) >= 2:
        user_states[chat_id]['name'] = name
        bot.send_message(chat_id, "Ismingiz qabul qilindi! Yaxshi!")
        ask_age(chat_id)
    else:
        bot.send_message(chat_id, "Iltimos, to'g'ri ism kiriting (faqat harflar, masalan: Abduvali Abdumuratov)!")

# Step 3: Ask for age
def ask_age(chat_id):
    bot.send_message(chat_id, "Yoshingizni kiriting:")
    user_states[chat_id]['step'] = 'get_age'

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'get_age')
def handle_age(message):
    chat_id = message.chat.id
    age = message.text.strip()

    if age.isdigit() and 10 <= int(age) <= 100:
        user_states[chat_id]['age'] = int(age)
        bot.send_message(chat_id, "Yoshingiz saqlandi! Juda yaxshi!")
        if user_states[chat_id]['service'] == "Consulting":
            ask_language_test(chat_id)
        else:
            user_states[chat_id]['language_test'] = "N/A"
            ask_phone_number(chat_id)
    else:
        bot.send_message(chat_id, "Iltimos, to'g'ri yosh kiriting (faqat raqamlar)!")

# Step 4: Ask about IELTS/TOPIK (only for Consulting)
def ask_language_test(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn1 = types.KeyboardButton("Ha")
    btn2 = types.KeyboardButton("Yo'q")
    markup.add(btn1, btn2)

    bot.send_message(chat_id, "IELTS yoki TOPIK sertifikatingiz bormi?", reply_markup=markup)
    user_states[chat_id]['step'] = 'get_language_test'

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'get_language_test')
def handle_language_test(message):
    chat_id = message.chat.id
    text = message.text

    if text == "Ha":
        bot.send_message(chat_id, "Juda yaxshi!")
        bot.send_message(chat_id, "Sertifikat darajasini kiriting (masalan: IELTS 6.5, TOPIK 4):")
        user_states[chat_id]['step'] = 'get_test_level'
    elif text == "Yo'q":
        bot.send_message(chat_id, "Havotirga o'rin yo'q!")
        user_states[chat_id]['language_test'] = "Yo'q"
        ask_phone_number(chat_id)
    else:
        bot.send_message(chat_id, "Iltimos tugmalardan birini tanlang!")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'get_test_level')
def handle_test_level(message):
    chat_id = message.chat.id
    level = message.text.strip()

    if re.match(r'^(IELTS\s[0-9](\.[0-9])?|TOPIK\s[1-6])$', level):
        user_states[chat_id]['language_test'] = level
        bot.send_message(chat_id, "Daraja qayd etildi! Ajoyib!")
        ask_phone_number(chat_id)
    else:
        bot.send_message(chat_id, "Iltimos, to'g'ri daraja kiriting (masalan: IELTS 6.5 yoki TOPIK 4)!")

# Step 5: Ask for phone number
def ask_phone_number(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = types.KeyboardButton("Telefon raqamimni yuborish", request_contact=True)
    markup.add(btn)

    bot.send_message(chat_id, "Telefon raqamingizni yuboring:", reply_markup=markup)
    user_states[chat_id]['step'] = 'get_phone'

@bot.message_handler(content_types=['contact'], func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'get_phone')
def handle_phone(message):
    chat_id = message.chat.id
    phone = message.contact.phone_number

    user_states[chat_id]['phone'] = phone
    bot.send_message(chat_id, "Telefon raqamingiz qabul qilindi! Zo'r!")
    save_user_data(chat_id)
    send_social_links(chat_id)

# Save user data to JSON file
def save_user_data(chat_id):
    user_data = {
        'chat_id': chat_id,
        'service': user_states[chat_id]['service'],
        'name': user_states[chat_id]['name'],
        'age': user_states[chat_id]['age'],
        'language_test': user_states[chat_id]['language_test'],
        'phone': user_states[chat_id]['phone']
    }
    registered_users.append(user_data)

    with open(USER_DATA_FILE, 'w') as f:
        json.dump(registered_users, f, indent=4, ensure_ascii=False)

    del user_states[chat_id]

# Send social media links
def send_social_links(chat_id):
    bot.send_message(chat_id, 
                     "Ro'yxatdan o'tganingiz uchun rahmat, biz siz bilan tez orada bog'lanamiz!\n"
                     "Yangilik va qulay imkoniyatlardan xabardor bo'lib turish uchun ijtimoiy tarmoqlarimizga obuna bo'ling:\n"
                     "Telegram: https://t.me/smartway_edu\n"
                     "Instagram: https://www.instagram.com/smartway_edu?igsh=MWN1OGVycGlscTg2Mg==",
                     reply_markup=types.ReplyKeyboardRemove(),
                     parse_mode=None)

# Handle unexpected messages
@bot.message_handler(func=lambda message: True)
def handle_unexpected(message):
    if message.chat.id in user_states:
        bot.send_message(message.chat.id, "Iltimos, jarayonni oxirigacha yakunlang!")
    else:
        bot.send_message(message.chat.id, "Botni ishga tushirish uchun /start buyrug'ini yuboring!")

# Webhook routes
@server.route('/' + bot.token, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@server.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{bot.token}")
    return "Webhook set!", 200

# Start the server
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{bot.token}")
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))