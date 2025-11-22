import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import feedparser
import time
import schedule
import threading
import os
from flask import Flask, request

# ================= CONFIGURATION =================
BOT_TOKEN = '8437898969:AAFI05v0qLbUteunnv7IXnlNpb1ZDUAp3y0'

# LIST OF CHANNELS TO POST TO (Add as many as you want)
# The bot must be an ADMIN in ALL of these channels
CHANNEL_LIST = ['@nwaezedavid_channel', '@internetparrot']

MASTERCLASS_LINK = "https://www.funnelhackingsecrets.com?cf_affiliate_id=4317627&affiliate_id=4317627"
YOUTUBE_RSS = "https://www.youtube.com/feeds/videos.xml?channel_id=UCncE7a4a4I3cBIvZAhnciag"
BLOG_RSS = "https://nwaezedavid.com/feed"

DB_FILE = "sent_links.txt"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ================= HELPER FUNCTIONS =================
def get_sent_links():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, 'r') as f:
        return f.read().splitlines()

def save_sent_link(link):
    with open(DB_FILE, 'a') as f:
        f.write(link + "\n")

# ================= FEATURE 1: HIGH-CONVERSION CLOSING (The Listener) =================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_first_name = message.from_user.first_name
    
    # 🧠 PSYCHOLOGICAL TACTIC USED:
    # 1. Validation ("You made it") - Makes them feel successful immediately.
    # 2. The "Hard Truth" (Pain point) - Separates them from "failures".
    # 3. The "Missing Link" (Solution) - Your Masterclass.
    # 4. Urgency/Exclusivity - "Don't close this".
    
    closing_copy = (
        f"🔥 **{user_first_name}, you made it.**\n\n"
        "Most people talk about making money online, but 99% never take the first step. "
        "The fact that you are here tells me you are in the **1% who are serious.**\n\n"
        "But here is the hard truth: \n"
        "Information without a **BLUEPRINT** is just noise. You don't need more 'tips', "
        "you need a proven system.\n\n"
        "I am inviting you to the **Online Income Masterclass**. This is the exact framework "
        "used to build 7-figure funnels.\n\n"
        "👇 **This is your bridge to financial freedom. Do not ignore it.**"
    )

    markup = InlineKeyboardMarkup()
    # Button 1: The Money Link (Primary Call to Action)
    btn_masterclass = InlineKeyboardButton("🔓 UNLOCK MY ACCESS NOW", url=MASTERCLASS_LINK)
    
    # Button 2: The Updates (Secondary Action)
    # We use the first channel in your list as the main "Updates" channel for them to join
    primary_channel_link = f"https://t.me/{CHANNEL_LIST[0].replace('@', '')}"
    btn_channel = InlineKeyboardButton("📢 Join Updates Channel", url=primary_channel_link)
    
    markup.add(btn_masterclass)
    markup.add(btn_channel)

    bot.send_message(message.chat.id, closing_copy, parse_mode='Markdown', reply_markup=markup)

# ================= FEATURE 2: DUAL-CHANNEL BROADCASTER =================

def check_and_post_feed(feed_url, source_name):
    """Parses RSS feed and posts new items to ALL channels."""
    try:
        feed = feedparser.parse(feed_url)
        sent_links = get_sent_links()
        
        if feed.entries:
            latest_entry = feed.entries[0]
            link = latest_entry.link
            title = latest_entry.title
            
            if link not in sent_links:
                # Construct the post message
                if source_name == "YouTube":
                    msg = f"🔴 **NEW VIDEO ALERT**\n\n{title}\n\n👇 Watch here:\n{link}"
                else:
                    msg = f"📝 **NEW BLOG POST**\n\n{title}\n\n👇 Read more:\n{link}"
                
                # LOOP THROUGH ALL CHANNELS AND POST
                for channel in CHANNEL_LIST:
                    try:
                        bot.send_message(channel, msg, parse_mode='Markdown')
                        print(f"Posted to {channel}: {title}")
                    except Exception as e:
                        print(f"Failed to post to {channel}: {e}")
                
                # Save to DB after attempting to post
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
    return "Bot is running and broadcasting to multiple channels!"

if __name__ == '__main__':
    t1 = threading.Thread(target=run_scheduler)
    t1.start()
    
    t2 = threading.Thread(target=run_bot)
    t2.start()
    
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

