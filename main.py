import os
try:
    import telebot
except ImportError:
    os.system('pip install pyTelegramBotAPI requests Flask')
    import telebot

import requests
import json
import base64
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home():
    return "Sanad Bot is Active!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# حقن التوكن والمفتاح الأمريكي الجديد مباشرة داخل الكود لضمان تخطي أي حظر أو قيود
TELEGRAM_TOKEN = "8969525324:AAHVTIBIYSeQrS3zjAlaMPGGEIevWPRL39k"
GEMINI_API_KEY = "AQ.Ab8RN6LPrR-LUo3GEK78v41hPSNnt-RLnbwTTXYfRywTGBnsyg"

MY_CRYPTO_WALLET = "TN6T6vQg9qWqgpRC511kS6b5hSkEnKyJyF"
ADMIN_CHAT_ID = 8840372128

bot = telebot.TeleBot(TELEGRAM_TOKEN, skip_pending=True)
user_attempts = {}
vip_users = set()

def main_menu():
    markup = telebot.types.InlineKeyboardMarkup()
    btn_use = telebot.types.InlineKeyboardButton("📝 البدء في التلخيص والكتابة", callback_data="start_chat")
    btn_vip = telebot.types.InlineKeyboardButton("💎 الاشتراك في الباقة المميزة", callback_data="premium_info")
    markup.add(btn_use, btn_vip)
    return markup

def admin_buttons(target_user_id):
    markup = telebot.types.InlineKeyboardMarkup()
    btn_accept = telebot.types.InlineKeyboardButton("✅ تفعيل VIP فوري", callback_data=f"vip_accept_{target_user_id}")
    btn_reject = telebot.types.InlineKeyboardButton("❌ رفض الطلب", callback_data=f"vip_reject_{target_user_id}")
    markup.add(btn_accept, btn_reject)
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    user_id = message.chat.id
    username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد معرف"
    
    try:
        if user_id not in user_attempts:
            user_attempts[user_id] = 0
            new_user_alert = (
                f"👤 *مستخدم جديد دخل البوت الآن!*\n\n"
                f"• الاسم: {message.from_user.first_name}\n"
                f"• المعرف: {username}\n"
                f"• الآيدي: `{user_id}`"
            )
            bot.send_message(ADMIN_CHAT_ID, new_user_alert, parse_mode="Markdown")
    except:
        pass

    welcome_text = (
        "🌟 أهلاً بك في بوت السند الرقمي AI المساعد الذكي المتكامل!\n\n"
        "أنا هنا لمساعدتك في تلخيص المحاضرات وحل الواجبات باللغة العربية.\n\n"
        "🎁 نمنحك *3 محاولات مجانية كاملة* لتجربة دقة الذكاء الاصطناعي.\n\n"
        "اضغط على الأزرار أدناه للبدء:"
    )
    bot.send_message(user_id, welcome_text, reply_markup=main_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    data = call.data
    
    if data == "start_chat":
        bot.send_message(user_id, "📝 رائع! أرسل لي الآن النص الطويل الذي تريد تلخيصه, أو اكتب سؤالك مباشرة.")
    elif data == "premium_info":
        send_payment_message(user_id)
    elif data.startswith("vip_accept_") and call.from_user.id == ADMIN_CHAT_ID:
        target_id = int(data.split("_")[-1])
        vip_users.add(target_id)
        bot.send_message(target_id, "🎉 *تهانينا! تم فحص التحويل وتفعيل اشتراكك في الباقة المميزة VIP بنجاح. يمكنك الآن استخدام البوت بلا حدود مدى الحياة!*", parse_mode="Markdown")
        bot.answer_callback_query(call.id, "✅ تم التفعيل!")
    elif data.startswith("vip_reject_") and call.from_user.id == ADMIN_CHAT_ID:
        target_id = int(data.split("_")[-1])
        bot.send_message(target_id, "❌ *عذراً، رفضت الإدارة طلب التفعيل لعدم تطابق بيانات التحويل.*", parse_mode="Markdown")
        bot.answer_callback_query(call.id, "❌ تم الرفض!")

def send_payment_message(user_id):
    premium_text = (
        "🔒 *عذراً، انتهت محاولاتك المجانية!*\n\n"
        "💎 للاشتراك في الباقة المميزة VIP وفتح البوت بلا حدود مدى الحياة:\n"
        "💵 قيمة الاشتراك الثابت: *5$ USDT* فقط لا غير.\n\n"
        f"قم بتحويل مبلغ الاشتراك إلى محفظة (TRC20) التالية بلمسة واحدة لنسخها:\n\n`{MY_CRYPTO_WALLET}`\n\n"
        "📥 بعد إتمام التحويل، التقط لقطة شاشة لعملية الدفع وأرسلها كصورة هنا فوراً ليتم تفعيل حسابك!"
    )
    bot.send_message(user_id, premium_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_gemini_ai(message):
    user_id = message.chat.id
    if user_id != ADMIN_CHAT_ID and user_id not in vip_users:
        if user_attempts.get(user_id, 0) >= 3:
            send_payment_message(user_id)
            return
        user_attempts[user_id] = user_attempts.get(user_id, 0) + 1

    status_msg = bot.reply_to(message, "⏳ جاري التفكير والتلخيص...")
    
    url = f"https://googleapis.com{GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": f"اكتب باللغة العربية وباحترافية عالية تفصيلية ومقنعة: {message.text}"}]}]}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=20)
        ai_result = response.json()['candidates']['content']['parts']['text']
    except Exception as e:
        ai_result = "❌ واجهت مشكلة في الاتصال بخوادم الذكاء الاصطناعي، يرجى المحاولة بعد قليل أو التأكد من إعدادات المفتاح."

    try:
        bot.delete_message(user_id, status_msg.message_id)
    except:
        pass
    bot.send_message(user_id, ai_result, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def handle_payment_screenshot(message):
    user_id = message.chat.id
    username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد معرف"
    bot.reply_to(message, "📥 تم استلام إثبات الدفع! جاري مراجعة المعاملة من قبل الإدارة وتفعيل حسابك VIP خلال دقائق معدودة.")
    
    photo_id = message.photo[-1].file_id
    caption_text = (
        f"💰 *تنبيه تحويل مالي جديد (5$)!* 💰\n\n"
        f"👤 *الطالب:* {message.from_user.first_name}\n"
        f"• المعرف: {username}\n"
        f"• الآيدي: `{user_id}`\n\n"
        f"قم بفتح محفظتك والتأكد، ثم اضغط على خيار التحكم أدناه لتفعيل حساب الطالب فوراً وبنقرة واحدة:"
    )
    try:
        bot.send_photo(ADMIN_CHAT_ID, photo_id, caption=caption_text, reply_markup=admin_buttons(user_id), parse_mode="Markdown")
    except:
        pass

if __name__ == '__main__':
    try:
        bot.remove_webhook()
    except:
        pass
    t = Thread(target=run)
    t.start()
    print("🚀 البوت يعمل الآن بنجاح في السحاب...")
    bot.infinity_polling(none_stop=True)




