import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import feedparser
import time
import schedule
import threading
import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask

# ================= CONFIGURATION =================
# 1. YOUR CREDENTIALS (Pre-filled)
BOT_TOKEN = '8437898969:AAFI05v0qLbUteunnv7IXnlNpb1ZDUAp3y0'

# 2. YOUR CHANNEL (Must start with @)
# Bot must be an ADMIN here
CHANNEL_LIST = ['@nwaezedavid_channel']

# 3. YOUR LINKS
MASTERCLASS_LINK = "https://www.funnelhackingsecrets.com?cf_affiliate_id=4317627&affiliate_id=4317627"
YOUTUBE_RSS = "https://www.youtube.com/feeds/videos.xml?channel_id=UCncE7a4a4I3cBIvZAhnciag"
BLOG_RSS = "https://nwaezedavid.com/feed"

# FILES
DB_FILE = "bot_database.db"
SENT_LINKS_FILE = "sent_links.txt"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ================= THE 7-DAY SOAP OPERA SEQUENCE =================
SEQUENCE_MESSAGES = {
    1: "👋 **Day 1 Check-in:**\n\nHey {name}, motivation fades, but systems don't.\n\nThe **Online Income Masterclass** isn't just a course; it's a system designed to generate revenue on autopilot.\n\n👇 **Don't let this opportunity slide:**",
    2: "🛑 **Stop working so hard.**\n\nThe 'hustle' is a lie. The top 1% aren't working 24/7; they are **Funnel Hacking**.\n\nThey simply copy what works. Why aren't you?\n\n👇 **Learn the secret here:**",
    3: "🚀 **Look at this...**\n\nI just saw a student hit their first **$1k month** using the exact framework inside the Masterclass.\n\nThey had no product and no experience. If they can do it, what is stopping you?",
    4: "🔥 **The gap is widening.**\n\nEvery day you wait, the internet gets smarter. The Masterclass teaches you how to stay ahead of the curve.\n\n👇 **Get the blueprint before you get left behind:**",
    5: "💡 **Quick Tip:**\n\nTraffic is easy. Conversion is hard.\n\nThe Masterclass solves the conversion problem for you. It's the missing key to your lock.\n\n👇 **Unlock it now:**",
    6: "🤔 **Still on the fence?**\n\nYou might be thinking, 'Is this for me?'\n\nIf you want to make money online but feel overwhelmed by 'tech', then **YES**. This is the blueprint. Zero guesswork.",
    7: "👋 **Last Call, {name}.**\n\nI won't bug you about this again. You have two choices:\n1. Keep guessing and struggling.\n2. Get the blueprint and scale.\n\n👇 **Make the right choice:**"
}

# ================= DATABASE MANAGER =================
def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, first_name TEXT, join_date TEXT, last_sequence_day INTEGER)''')
    conn.commit()
    conn.close()

def add_user(user_id, first_name):
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if c.fetchone() is None:
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute("INSERT INTO users VALUES (?, ?, ?, 0)", (user_id, first_name, today))
        conn.commit()
        print(f"New user added: {first_name}")
    conn.close()

def get_all_users():
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT * FROM users")
        users = c.fetchall()
        conn.close()
        return users
    except:
        return []

def update_user_sequence(user_id, day):
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute("UPDATE users SET last_sequence_day=? WHERE user_id=?", (day, user_id))
    conn.commit()
    conn.close()

init_db()

# ================= LOGIC: GATEKEEPER & WELCOME =================
def check_membership(user_id):
    """Checks if user is a member of the channel"""
    for channel in CHANNEL_LIST:
        try:
            # Check user status in the channel
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['creator', 'administrator', 'member']:
                return False
        except Exception as e:
            # If error (e.g., bot is not admin), print error but assume False
            print(f"Membership check error for {channel}: {e}")
            return False
    return True

def send_masterclass_access(chat_id, first_name):
    msg = (
        f"🔥 **{first_name}, Access Granted.**\n\n"
        "Most people never take this step. You are now in the **1%**.\n\n"
        "Here is the hard truth: Information without a **BLUEPRINT** is just noise. "
        "👇 **Click below to enter the Masterclass:**"
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔓 UNLOCK ACCESS NOW", url=MASTERCLASS_LINK))
    bot.send_message(chat_id, msg, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    # 1. Add to Database
    add_user(user_id, first_name)
    
    # 2. Check Channel Membership
    if check_membership(user_id):
        send_masterclass_access(message.chat.id, first_name)
    else:
        # Force Subscribe Message
        msg = "🔒 **ACCESS LOCKED**\n\nTo access the **Masterclass**, you must join our updates channel first."
        markup = InlineKeyboardMarkup()
        
        for channel in CHANNEL_LIST:
            url_name = channel.replace("@", "")
            # Telegram Link format
            markup.add(InlineKeyboardButton(f"👉 Join {channel}", url=f"https://t.me/{url_name}"))
            
        markup.add(InlineKeyboardButton("✅ I Have Joined", callback_data="check_sub"))
        bot.send_message(message.chat.id, msg, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_verify(call):
    if check_membership(call.from_user.id):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        send_masterclass_access(call.message.chat.id, call.from_user.first_name)
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined the channel yet!")

# ================= FEATURE 2: 7-DAY SEQUENCE SCHEDULER =================
def run_daily_sequence():
    """Sends the soap opera sequence messages"""
    print("Running daily sequence check...")
    users = get_all_users()
    
    for user in users:
        user_id, first_name, join_date_str, last_day = user
        
        try:
            join_date = datetime.strptime(join_date_str, "%Y-%m-%d")
            days_since_join = (datetime.now() - join_date).days
            
            # If days_since_join matches a sequence day, and we haven't sent it yet
            if 0 < days_since_join <= 7 and days_since_join > last_day:
                msg_text = SEQUENCE_MESSAGES.get(days_since_join).format(name=first_name)
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("🚀 Access Masterclass", url=MASTERCLASS_LINK))
                
                bot.send_message(user_id, msg_text, parse_mode='Markdown', reply_markup=markup)
                print(f"Sent Day {days_since_join} to {first_name}")
                
                update_user_sequence(user_id, days_since_join)
        except Exception as e:
            print(f"Sequence error for {first_name}: {e}")

# ================= FEATURE 3: AUTO BROADCASTER =================
def get_sent_links():
    if not os.path.exists(SENT_LINKS_FILE): return []
    with open(SENT_LINKS_FILE, 'r') as f: return f.read().splitlines()

def save_sent_link(link):
    with open(SENT_LINKS_FILE, 'a') as f: f.write(link + "\n")

def check_feed():
    # Loop through YouTube and Blog
    for source, name in [(YOUTUBE_RSS, "YouTube"), (BLOG_RSS, "Blog")]:
        try:
            feed = feedparser.parse(source)
            if feed.entries:
                entry = feed.entries[0]
                # If link is new
                if entry.link not in get_sent_links():
                    if name == "YouTube":
                        msg = f"🔴 **NEW VIDEO ALERT**\n\n{entry.title}\n\n👇 Watch here:\n{entry.link}"
                    else:
                        msg = f"📝 **NEW BLOG POST**\n\n{entry.title}\n\n👇 Read more:\n{entry.link}"
                    
                    # Send to Channel
                    for ch in CHANNEL_LIST: 
                        try: 
                            bot.send_message(ch, msg, parse_mode='Markdown') 
                            print(f"Posted {name} to {ch}")
                        except Exception as e: 
                            print(f"Broadcaster Error: {e}")
                            
                    save_sent_link(entry.link)
        except Exception as e:
             print(f"Feed Error: {e}")

# ================= SCHEDULER & FLASK SERVER =================
def scheduler_thread():
    # Check RSS feeds every 10 minutes
    schedule.every(10).minutes.do(check_feed)
    
    # Run the 7-Day Sequence once every 24 hours
    # You can adjust "10:00" to your preferred time
    schedule.every().day.at("10:00").do(run_daily_sequence)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/')
def index():
    return "Nwaeze David Bot is Running 24/7!"

if __name__ == '__main__':
    # Start Scheduler Thread
    t1 = threading.Thread(target=scheduler_thread)
    t1.start()
    
    # Start Bot Polling Thread
    t2 = threading.Thread(target=bot.infinity_polling)
    t2.start()
    
    # Start Flask Web Server (for Render)
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
    
