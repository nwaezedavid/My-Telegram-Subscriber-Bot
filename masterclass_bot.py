import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import feedparser
import time
import schedule
import threading
import os
from flask import Flask, request

# ================= CONFIGURATION =================
BOT_TOKEN = 'YOUR_BOT_TOKEN_FROM_BOTFATHER'
CHANNEL_USERNAME = '@YOUR_CHANNEL_USERNAME' 

MASTERCLASS_LINK = "https://www.funnelhackingsecrets.com?cf_affiliate_id=4317627&affiliate_id=4317627"
YOUTUBE_RSS = "https://www.youtube.com/feeds/videos.xml?channel_id=UCncE7a4a4I3cBIvZAhnciag"
BLOG_RSS = "https://nwaezedavid.com/feed"
DB_FILE = "sent_links.txt"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__) # Create the fake web server

# ================= HELPER FUNCTIONS =================
def get_sent_links():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, 'r') as f:
        return f.read().splitlines()

def save_sent_link(link):
    with open(DB_FILE, 'a') as f:
        f.write(link + "\n")

# ================= FEATURE 1: NEW USER CONVERSION =================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_first_name = message.from_user.first_name
    welcome_text = (
        f"Hi {user_first_name}! 👋\n\n"
        "You have successfully subscribed to my updates.\n\n"
        "⚠️ **BEFORE YOU GO:**\n"
        "If you are serious about generating real income online, "
        "I have something important for you.\n\n"
        "Click the button below to access the **Online Income Masterclass** "
        "and learn the secrets to funnel hacking."
    )
    markup = InlineKeyboardMarkup()
    btn_masterclass = InlineKeyboardButton("🚀 Access Masterclass NOW", url=MASTERCLASS_LINK)
    markup.add(btn_masterclass)
    btn_channel = InlineKeyboardButton("📢 Join Updates Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")
    markup.add(btn_channel)
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=markup)

# ================= FEATURE 2: BROADCASTER =================
def check_and_post_feed(feed_url, source_name):
    try:
        feed = feedparser.parse(feed_url)
        sent_links = get_sent_links()
        if feed.entries:
            latest_entry = feed.entries[0]
            link = latest_entry.link
            title = latest_entry.title
            if link not in sent_links:
                if source_name == "YouTube":
                    msg = f"🔴 **NEW VIDEO ALERT**\n\n{title}\n\n👇 Watch here:\n{link}"
                else:
                    msg = f"📝 **NEW BLOG POST**\n\n{title}\n\n👇 Read more:\n{link}"
                bot.send_message(CHANNEL_USERNAME, msg, parse_mode='Markdown')
                save_sent_link(link)
    except Exception as e:
        print(f"Error checking {source_name} feed: {e}")

def job():
    check_and_post_feed(YOUTUBE_RSS, "YouTube")
    check_and_post_feed(BLOG_RSS, "Blog")

def run_scheduler():
    schedule.every(10).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)

def run_bot():
    bot.infinity_polling()

# ================= WEB SERVER FOR RENDER =================
@app.route('/')
def index():
    return "Bot is running!"

if __name__ == '__main__':
    # Start Scheduler in a separate thread
    t1 = threading.Thread(target=run_scheduler)
    t1.start()
    
    # Start Bot Listener in a separate thread
    t2 = threading.Thread(target=run_bot)
    t2.start()
    
    # Start Web Server (Main Thread)
    # Render assigns a port automatically via the PORT env var
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)