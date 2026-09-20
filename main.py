import os
import telebot

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if ADMIN_ID:
    try:
        ADMIN_ID = int(ADMIN_ID)
    except ValueError:
        ADMIN_ID = None

bot = telebot.TeleBot(TOKEN)

waiting_users = []
active_pairs = {}
all_users = set()
banned_users = set()

def is_banned(user_id):
    return user_id in banned_users

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    all_users.add(user_id)
    
    if is_banned(user_id):
        bot.send_message(user_id, "❌ حساب کاربری شما مسدود شده است.")
        return

    msg = "به ربات چت ناشناس خوش آمدید!\nبرای پیدا کردن هم‌صحبت دستور /search را بزنید."
    if user_id == ADMIN_ID:
        msg += "\n\n👑 شما ادمین هستید. برای ورود به پنل دستور /admin را ارسال کنید."
    
    bot.send_message(user_id, msg)

@bot.message_handler(commands=['search'])
def search_partner(message):
    user_id = message.chat.id
    if is_banned(user_id):
        bot.send_message(user_id, "❌ شما مسدود شده‌اید.")
        return

    if user_id in active_pairs:
        bot.send_message(user_id, "شما در حال حاضر در یک چت هستید!")
        return
    if user_id in waiting_users:
        bot.send_message(user_id, "شما قبلاً در صف انتظار قرار گرفته‌اید.")
        return

    if len(waiting_users) > 0:
        partner_id = waiting_users.pop(0)
        active_pairs[user_id] = partner_id
        active_pairs[partner_id] = user_id
        bot.send_message(user_id, "هم‌صحبت پیدا شد! می‌توانید گفتگو را شروع کنید.\nبرای پایان دستور /stop را بزنید.")
        bot.send_message(partner_id, "هم‌صحبت پیدا شد! می‌توانید گفتگو را شروع کنید.\nبرای پایان دستور /stop را بزنید.")
    else:
        waiting_users.append(user_id)
        bot.send_message(user_id, "در حال جستجوی هم‌صحبت... لطفاً منتظر بمانید.")

@bot.message_handler(commands=['stop'])
def stop_chat(message):
    user_id = message.chat.id
    if user_id in active_pairs:
        partner_id = active_pairs.pop(user_id)
        active_pairs.pop(partner_id, None)
        bot.send_message(user_id, "چت پایان یافت.")
        bot.send_message(partner_id, "هم‌صحبت شما چت را پایان داد.")
    elif user_id in waiting_users:
        waiting_users.remove(user_id)
        bot.send_message(user_id, "از صف انتظار خارج شدید.")
    else:
        bot.send_message(user_id, "شما در حال حاضر در چتی نیستید.")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.chat.id
    if user_id != ADMIN_ID:
        return

    panel_text = (
        "⚙️ **پنل مدیریت ربات**\n\n"
        "📊 `/stats` - مشاهده آمار کامل ربات\n"
        "📢 `/broadcast <متن>` - ارسال پیام همگانی\n"
        "🚫 `/ban <user_id>` - مسدود کردن کاربر\n"
        "✅ `/unban <user_id>` - رفع مسدودی کاربر\n"
    )
    bot.send_message(user_id, panel_text, parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    if message.chat.id != ADMIN_ID:
        return
    
    active_chats_count = len(active_pairs) // 2
    stats_msg = (
        f"📊 **آمار ربات:**\n\n"
        f"👥 کل کاربران: {len(all_users)}\n"
        f"⏳ افراد در صف انتظار: {len(waiting_users)}\n"
        f"💬 چت‌های فعال: {active_chats_count}\n"
        f"🚫 کاربران مسدود شده: {len(banned_users)}"
    )
    bot.send_message(message.chat.id, stats_msg, parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def admin_broadcast(message):
    if message.chat.id != ADMIN_ID:
        return
    
    text = message.text.replace('/broadcast', '').strip()
    if not text:
        bot.send_message(ADMIN_ID, "لطفاً متن پیام را وارد کنید.\nمثال: `/broadcast سلام به همه`", parse_mode="Markdown")
        return

    count = 0
    for u_id in list(all_users):
        try:
            bot.send_message(u_id, f"📢 **پیام مدیریت:**\n\n{text}", parse_mode="Markdown")
            count += 1
        except Exception:
            pass
    bot.send_message(ADMIN_ID, f"✅ پیام به {count} کاربر ارسال شد.")

@bot.message_handler(commands=['ban'])
def admin_ban(message):
    if message.chat.id != ADMIN_ID:
        return
    
    try:
        target_id = int(message.text.split()[1])
        banned_users.add(target_id)
        
        if target_id in active_pairs:
            partner_id = active_pairs.pop(target_id)
            active_pairs.pop(partner_id, None)
            bot.send_message(partner_id, "هم‌صحبت شما از ربات مسدود شد و چت پایان یافت.")
        if target_id in waiting_users:
            waiting_users.remove(target_id)
            
        bot.send_message(ADMIN_ID, f"🚫 کاربر {target_id} با موفقیت مسدود شد.")
    except Exception:
        bot.send_message(ADMIN_ID, "فرمت اشتباه است. دستور به این صورت است:\n`/ban 123456789`", parse_mode="Markdown")

@bot.message_handler(commands=['unban'])
def admin_unban(message):
    if message.chat.id != ADMIN_ID:
        return
    
    try:
        target_id = int(message.text.split()[1])
        banned_users.discard(target_id)
        bot.send_message(ADMIN_ID, f"✅ کاربر {target_id} رفع مسدودی شد.")
    except Exception:
        bot.send_message(ADMIN_ID, "فرمت اشتباه است. دستور به این صورت است:\n`/unban 123456789`", parse_mode="Markdown")

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'voice', 'sticker', 'video'])
def handle_messages(message):
    user_id = message.chat.id
    if is_banned(user_id):
        return

    if user_id in active_pairs:
        partner_id = active_pairs[user_id]
        bot.copy_message(chat_id=partner_id, from_chat_id=user_id, message_id=message.message_id)
    else:
        bot.send_message(user_id, "شما به کسی متصل نیستید. برای جستجو /search را بزنید.")

bot.infinity_polling()
