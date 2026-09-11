import os
import sys
import io
from threading import Thread
from flask import Flask

# التثبيت التلقائي للمكتبات لضمان عدم توقف السيرفر
try:
    import telebot
    import google.generativeai as genai
    from PIL import Image
except ImportError:
    os.system('pip install pyTelegramBotAPI google-generativeai Flask requests pillow')
    import telebot
    import google.generativeai as genai
    from PIL import Image

# قراءة المفاتيح ومتغيرات البيئة
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
MY_CRYPTO_WALLET = os.environ.get("WALLET_ADDRESS", "TN6T6vQg9qWqgpRC511kS6b5hSkEnKyJyF")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "8840372128"))

# خادم Flask لإبقاء الخدمة نشطة على Render
app = Flask('')

@app.route('/')
def home():
    return "Sanad Scientific Encyclopedia Bot is Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# تهيئة الذكاء الاصطناعي Gemini 1.5 Flash
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# تهيئة بوت تلغرام
bot = telebot.TeleBot(TELEGRAM_TOKEN, skip_pending=True)

# قاعدة البيانات المؤقتة للذاكرة
user_attempts = {}
vip_users = set()

# التوجيهات الأكاديمية والأخلاقية الصارمة
SYSTEM_PROMPT = """
أنت الموسوعة العلمية والأكاديمية الشاملة والمساعد الذكي لطلاب المدارس، الجامعات، ومرحلة الماجستير والدكتوراه.
مجالات الاختصاص: الطب والعلوم الصحية، العلوم الطبيعية، الهندسة، التكنولوجيا، الاقتصاد، إدارة الأعمال، والعمل الحر.

ضوابط أمان وأخلاقيات صارمة جداً (خط أحمر):
1. يمنع منعاً باتاً الإجابة عن أو توليد أو تحليل أي محتوى إباحي، جنسي، تعري، أو أي محتوى يسيء للنساء أو يشوه صورهن.
2. إذا احتوى الطلب أو الصورة على محتوى خادش أو غير أخلاقي، أجب بعبارة: "عذراً، هذا الطلب يخالف الشروط الأخلاقية والأكاديمية للموسوعة."
"""

def main_menu():
    markup = telebot.types.InlineKeyboardMarkup()
    btn_use = telebot.types.InlineKeyboardButton("🎓 ابدأ البحث والحل الأكاديمي", callback_data="start_chat")
    btn_vip = telebot.types.InlineKeyboardButton("💎 الاشتراك في الباقة المميزة ($5)", callback_data="premium_info")
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
                f"👤 *مستخدم جديد دخل الموسوعة العلمية!*\n\n"
                f"• الاسم: {message.from_user.first_name}\n"
                f"• المعرف: {username}\n"
                f"• الآيدي: `{user_id}`"
            )
            bot.send_message(ADMIN_CHAT_ID, new_user_alert, parse_mode="Markdown")
    except Exception as e:
        print(f"Error notifying admin: {e}")

    welcome_text = (
        "🎓 **أهلاً بك في الموسوعة العلمية والأكاديمية الذكية!**\n\n"
        "مساعدك الشامل في الطب، العلوم، الأعمال الحرة، الأبحاث الجامعية، والماجستير.\n\n"
        "🎁 نمنحك **3 محاولات مجانية كاملة** (نصوص أو تحليل صور ومخططات).\n\n"
        "اضغط أدناه أو أرسل سؤالك مباشرة:"
    )
    bot.send_message(user_id, welcome_text, reply_markup=main_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    data = call.data
    
    if data == "start_chat":
        bot.send_message(user_id, "📝 أرسل سؤالك الأكاديمي، أو قم بإرفاق صورة مسألة/رسم بياني لتصحيحها وحلها.")
    elif data == "premium_info":
        send_payment_message(user_id)
    elif data.startswith("vip_accept_") and call.from_user.id == ADMIN_CHAT_ID:
        target_id = int(data.split("_")[-1])
        vip_users.add(target_id)
        bot.send_message(target_id, "🎉 **تهانينا! تم فحص التحويل وتفعيل اشتراكك في الباقة المميزة VIP بنجاح. يمكنك الآن استخدام الموسوعة بلا حدود!**", parse_mode="Markdown")
        bot.answer_callback_query(call.id, "✅ تم التفعيل!")
    elif data.startswith("vip_reject_") and call.from_user.id == ADMIN_CHAT_ID:
        target_id = int(data.split("_")[-1])
        bot.send_message(target_id, "❌ **عذراً، رفضت الإدارة طلب التفعيل لعدم تطابق بيانات التحويل.**", parse_mode="Markdown")
        bot.answer_callback_query(call.id, "❌ تم الرفض!")

def send_payment_message(user_id):
    premium_text = (
        "🔒 **عذراً، انتهت محاولاتك المجانية الـ 3!**\n\n"
        "💎 للاشتراك في الباقة المميزة VIP وفتح استخدام الموسوعة بلا حدود:\n"
        "💵 قيمة الاشتراك: **5$ USDT** فقط.\n\n"
        f"عنوان المحفظة (TRC20):\n`{MY_CRYPTO_WALLET}`\n\n"
        "📥 **بعد التحويل، أرسل لقطة الشاشة للإيصال هنا مباشرة.**\n"
        "سيقوم الذكاء الاصطناعي بفحص الإيصال وإرساله للإدارة لتفعيل حسابك فوراً!"
    )
    bot.send_message(user_id, premium_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_gemini_ai(message):
    user_id = message.chat.id
    text = message.text

    forbidden = ["تعري", "جنس", "إباحي", "تشويه", "عارية"]
    if any(w in text.lower() for w in forbidden):
        bot.reply_to(message, "⛔ عذراً، هذا الطلب يخالف الشروط الأخلاقية والأكاديمية للموسوعة.")
        return

    if user_id != ADMIN_CHAT_ID and user_id not in vip_users:
        if user_attempts.get(user_id, 0) >= 3:
            send_payment_message(user_id)
            return
        user_attempts[user_id] = user_attempts.get(user_id, 0) + 1

    status_msg = bot.reply_to(message, "⏳ جاري البحث والتحليل الأكاديمي...")
    
    try:
        full_prompt = f"{SYSTEM_PROMPT}\n\nسؤال المستخدم: {text}"
        response = model.generate_content(full_prompt)
        ai_result = response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        ai_result = "❌ حدث خطأ أثناء الاتصال بالذكاء الاصطناعي، يرجى المحاولة لاحقاً."

    try:
        if len(ai_result) > 4000:
            bot.edit_message_text(ai_result[:4000], chat_id=user_id, message_id=status_msg.message_id)
            bot.send_message(user_id, ai_result[4000:])
        else:
            bot.edit_message_text(ai_result, chat_id=user_id, message_id=status_msg.message_id)
    except Exception as e:
        print(f"Telegram Edit Message Error: {e}")
        bot.send_message(user_id, ai_result)

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    user_id = message.chat.id
    username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد معرف"

    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    image = Image.open(io.BytesIO(downloaded_file))

    if user_id != ADMIN_CHAT_ID and user_id not in vip_users and user_attempts.get(user_id, 0) >= 3:
        bot.reply_to(message, "📥 تم استلام الإيصال! جاري تدقيق العملية بواسطة الذكاء الاصطناعي وإرسالها للإدارة...")
        
        receipt_prompt = "قم بفحص هذه الصورة وتأكيد ما إذا كانت إيصال تحويل مالي ناجح بمبلغ 5 دولار، واذكر النتيجة باختصار."
        try:
            check_res = model.generate_content([receipt_prompt, image])
            ai_analysis = check_res.text
        except Exception:
            ai_analysis = "تعذر الفحص الآلي للإيصال، يرجى التدقيق اليدوي."

        caption_text = (
            f"💰 *تنبيه تحويل مالي جديد (5$)!* 💰\n\n"
            f"👤 *المستخدم:* {message.from_user.first_name}\n"
            f"• المعرف: {username}\n"
            f"• الآيدي: `{user_id}`\n\n"
            f"🤖 *تدقيق الذكاء الاصطناعي للإيصال:*\n{ai_analysis}\n\n"
            f"يرجى التأكد والضغط على خيار التحكم أدناه:"
        )
        try:
            bot.send_photo(ADMIN_CHAT_ID, message.photo[-1].file_id, caption=caption_text, reply_markup=admin_buttons(user_id), parse_mode="Markdown")
        except Exception as e:
            print(f"Error sending photo to admin: {e}")
        return

    if user_id != ADMIN_CHAT_ID and user_id not in vip_users:
        user_attempts[user_id] = user_attempts.get(user_id, 0) + 1

    status_msg = bot.reply_to(message, "🔍 جاري قراءة وتحليل الصورة أكاديمياً...")
    caption = message.caption or ""
    
    academic_photo_prompt = f"{SYSTEM_PROMPT}\n\nقم بتحليل هذه الصورة علمياً وأكاديمياً وحل المسألة أو الشرح. ملاحظات: {caption}"

    try:
        response = model.generate_content([academic_photo_prompt, image])
        ai_result = response.text
    except Exception as e:
        print(f"Vision API Error: {e}")
        ai_result = "❌ حدث خطأ أثناء تحليل الصورة، يرجى التأكد من وضوح الصورة وتكرار المحاولة."

    try:
        if len(ai_result) > 4000:
            bot.edit_message_text(ai_result[:4000], chat_id=user_id, message_id=status_msg.message_id)
            bot.send_message(user_id, ai_result[4000:])
        else:
            bot.edit_message_text(ai_result, chat_id=user_id, message_id=status_msg.message_id)
    except Exception as e:
        bot.send_message(user_id, ai_result)

if __name__ == '__main__':
    try:
        bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        print(f"Error clearing webhook: {e}")
        
    t = Thread(target=run_flask)
    t.start()
    print("🚀 الموسوعة العلمية تعمل الآن بنجاح...")
    bot.infinity_polling(none_stop=True)















