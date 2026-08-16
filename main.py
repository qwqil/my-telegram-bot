from flask import Flask
from threading import Thread
import os


import telebot
from telebot import types
import requests
from urllib.parse import urlparse

BOT_TOKEN = "8659664050:AAF-4ZFyqGCm8r-YIlRN-B2cxsiimeZiyM4"
bot = telebot.TeleBot(BOT_TOKEN)

# تخزين لغة المستخدم (الافتراضي: عربي)
user_languages = {}

def analyze_url(url, lang='ar'):
    """دالة لفحص الرابط وترجمة التقرير حسب اللغة"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    report = []
    
    try:
        parsed = urlparse(url)
        domain_label = "🌐 **النطاق (Domain):**" if lang == 'ar' else "🌐 **Domain:**"
        report.append(f"{domain_label} `{parsed.netloc}`")
        
        # فحص بروتوكول التشفير
        if parsed.scheme == "https":
            enc_text = "🔒 **التشفير:** آمن (HTTPS)" if lang == 'ar' else "🔒 **Encryption:** Secure (HTTPS)"
        else:
            enc_text = "⚠️ **التشفير:** غير آمن (HTTP - احذر!)" if lang == 'ar' else "⚠️ **Encryption:** Unsecure (HTTP - Be careful!)"
        report.append(enc_text)

        # إرسال طلب للتأكد من حالة الرابط
        response = requests.get(url, timeout=5, allow_redirects=True)
        status_label = "📊 **رمز الحالة (Status Code):**" if lang == 'ar' else "📊 **Status Code:**"
        report.append(f"{status_label} `{response.status_code}`")
        
        # التحقق من وجود إعادة توجيه
        if len(response.history) > 0:
            redir_label = "🔄 **تحذير إعادة توجيه:** الرابط يحول إلى:" if lang == 'ar' else "🔄 **Redirect Warning:** The URL redirects to:"
            report.append(redir_label)
            report.append(f"`{response.url}`")

    except requests.exceptions.SSLError:
        err = "❌ **خطر:** شهادة الأمان SSL غير صالحة أو منتهية!" if lang == 'ar' else "❌ **Danger:** Invalid or Expired SSL Certificate!"
        report.append(err)
    except requests.exceptions.ConnectionError:
        err = "❌ **خطأ:** تعذر الاتصال بالرابط (رابط تعطل أو غير موجود)." if lang == 'ar' else "❌ **Error:** Could not connect (Dead link or invalid domain)."
        report.append(err)
    except requests.exceptions.Timeout:
        err = "⏳ **تحذير:** انتهت مهلة الاتصال." if lang == 'ar' else "⏳ **Warning:** Connection timed out."
        report.append(err)
    except Exception as e:
        report.append(f"⚠️ **Error:** {str(e)}")

    return "\n".join(report)

def get_language_keyboard():
    """إنشاء أزرار اختيار اللغة"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_ar = types.InlineKeyboardButton("العربية 🇸🇦", callback_data="lang_ar")
    btn_en = types.InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")
    markup.add(btn_ar, btn_en)
    return markup

@bot.message_handler(commands=['start', 'help', 'language'])
def send_welcome(message):
    welcome_text = (
        "مرحباً بك في **The Guard Web**! 🛡️\n"
        "الرجاء اختيار اللغة المفضلة / Please select your preferred language:"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown", reply_markup=get_language_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    lang = call.data.split('_')[1]
    user_languages[call.message.chat.id] = lang
    
    if lang == 'ar':
        msg = "تم اختيار اللغة **العربية** 🇸🇦\nأرسل أي رابط الآن وسأقوم بفحصه لك."
    else:
        msg = "Language set to **English** 🇬🇧\nSend me any link to scan it."
        
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_text = message.text.strip()
    chat_id = message.chat.id
    lang = user_languages.get(chat_id, 'ar') # العربية افتراضياً

    if "." in user_text:
        scan_msg = "🔍 جاري فحص الرابط..." if lang == 'ar' else "🔍 Scanning URL..."
        bot.reply_to(message, scan_msg)
        result = analyze_url(user_text, lang)
        bot.send_message(chat_id, result, parse_mode="Markdown")
    else:
        err_msg = "يرجى إرسال رابط صحيح (مثال: google.com)" if lang == 'ar' else "Please send a valid URL (e.g., google.com)."
        bot.reply_to(message, err_msg)

print("The Guard Web Bot is running with multi-language support...")
bot.infinity_polling()
