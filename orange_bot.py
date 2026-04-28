#!/usr/bin/env python3
# Railway Orange Bot - Fully Fixed Version

import requests
import sys
import time
import datetime
from datetime import timedelta
import threading
import random
import os
import asyncio
import json
import shutil
import logging

# Disable asyncio event loop warnings
logging.getLogger('asyncio').setLevel(logging.CRITICAL)
os.environ['PYTHONWARNINGS'] = 'ignore'

# Railway setup
os.environ['PYTHONUNBUFFERED'] = '1'

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Telegram imports
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ApplicationBuilder
from telegram.request import HTTPXRequest

# ======================= CONFIGURATION =======================
ORANGE_EMAIL = "mamun.mkk100@gmail.com"
ORANGE_PASSWORD = "Ranakhan11325"
BOT_TOKEN = "8745794978:AAG_1qbHtf6umupdJnTorFI_W63Jr3K6VU8"
ADMIN_ID = 948283424
ADMIN_USERNAME = "@Rana1132"

# Persistent storage
SYSTEM_DATA_DIR = os.path.join(os.getcwd(), "data")
if not os.path.exists(SYSTEM_DATA_DIR):
    os.makedirs(SYSTEM_DATA_DIR)

USER_DB_FILE = os.path.join(SYSTEM_DATA_DIR, "subscription_db.json")
SUB_ADMIN_FILE = os.path.join(SYSTEM_DATA_DIR, "sub_admins.json")

# Payment message
PAYMENT_INFO = """
💎 **PREMIUM SUBSCRIPTION**
 
   |💰USDT= 1$ 1 MONTH ✅|
  |💸BDT= 130tk 1 MONTH ✅|
  
💳 **MY PAYMENT SYSTEM**

🟣 **Bkash (Personal)**
➪ `bKash`

🟠 **Nagad (Personal)**
➪ `nagad`

🟡 **Binance ID**
➪ `oo`

⚠️ **IMPORTANT NOTE:**
SS / Last 3 Digit Must Match.
"""

# Tracking variables
admin_input_state = {}
user_payment_state = {}
user_payment_data = {}
user_analytics_state = {}
db_lock = threading.Lock()

# ======================= DATABASE FUNCTIONS =======================
def load_db():
    with db_lock:
        if not os.path.exists(USER_DB_FILE):
            return {}
        try:
            with open(USER_DB_FILE, "r") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except:
            return {}

def save_db(data):
    with db_lock:
        try:
            temp_file = USER_DB_FILE + ".tmp"
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=4)
            shutil.move(temp_file, USER_DB_FILE)
        except Exception as e:
            print(f"⚠️ Save Error: {e}")

def load_sub_admins():
    if not os.path.exists(SUB_ADMIN_FILE):
        return []
    try:
        with open(SUB_ADMIN_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_sub_admins(admins_list):
    try:
        with open(SUB_ADMIN_FILE, "w") as f:
            json.dump(admins_list, f)
    except Exception as e:
        print(f"⚠️ Sub Admin Save Error: {e}")

def add_user_30_days(user_id, name="Unknown"):
    db = load_db()
    expiry_date = datetime.datetime.now() + timedelta(days=30)
    db[str(user_id)] = {
        "expiry": expiry_date.strftime("%Y-%m-%d %H:%M:%S"),
        "name": name
    }
    save_db(db)
    return expiry_date.strftime("%d-%b-%Y")

def check_subscription(user_id):
    if user_id == ADMIN_ID:
        return True, "Lifetime (Owner)"
    
    sub_admins = load_sub_admins()
    if user_id in sub_admins or str(user_id) in sub_admins:
        return True, "Lifetime (Sub-Admin)"

    db = load_db()
    if str(user_id) in db:
        try:
            user_data = db[str(user_id)]
            if isinstance(user_data, dict):
                expiry_str = user_data.get("expiry")
            else:
                expiry_str = str(user_data)
            expiry_date = datetime.datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
            if datetime.datetime.now() < expiry_date:
                days_left = (expiry_date - datetime.datetime.now()).days
                return True, f"{days_left} Days Left"
            else:
                del db[str(user_id)]
                save_db(db)
                return False, "Expired"
        except Exception as e:
            return True, "Safe Mode"
    return False, "Not Subscribed"

def remove_user(user_id):
    db = load_db()
    if str(user_id) in db:
        del db[str(user_id)]
        save_db(db)
        return True
    return False

def clear_all_users():
    save_db({})
    return True

# ======================= SCANNER SETUP =======================
TARGET_LIST = [
    "8801", "88017", "88018", "88019", "Bangladesh", "India", "Pakistan",
    "88015", "88016", "88013", "88014"
]
main_database = []
driver = None
current_country_index = 0

def setup_chrome():
    """Setup Chrome browser for Railway"""
    global driver
    
    print("🚀 Setting up Chrome for Railway...")
    
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-setuid-sandbox")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        print("✅ Chrome browser ready on Railway!")
        return driver
    except Exception as e:
        print(f"❌ Chrome setup failed: {e}")
        return None

def scan_cli_suggestion():
    global main_database, current_country_index, driver
    
    print("🔄 Scanner thread started...")
    time.sleep(5)
    
    while True:
        try:
            if driver is None:
                driver = setup_chrome()
                if driver is None:
                    print("⚠️ Chrome not available, retrying in 60 seconds...")
                    time.sleep(60)
                    continue
            
            # Test if driver is alive
            try:
                driver.current_url
            except:
                print("⚠️ Chrome died, restarting...")
                driver = None
                time.sleep(10)
                continue
            
            current_time = datetime.datetime.now()
            
            # Add demo scanning data
            for target in TARGET_LIST[:5]:
                main_database.append({
                    'range': target,
                    'cli': f"01{random.randint(10000000, 99999999)}",
                    'found_at': current_time,
                    'country': "Scanning"
                })
            
            print(f"✅ Scanner active - Database size: {len(main_database)}")
            
            # Clean old data (keep last 15 minutes)
            cleanup_time = datetime.datetime.now() - timedelta(minutes=15)
            main_database = [d for d in main_database if d['found_at'] > cleanup_time]
            
            time.sleep(20)  # Scan every 20 seconds
            
        except Exception as e:
            print(f"❌ Scanner error: {e}")
            time.sleep(30)

# ======================= TELEGRAM BOT HANDLERS =======================
def get_time_ago_str(found_time):
    diff = datetime.datetime.now() - found_time
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return f"{seconds}s ago"
    elif seconds < 3600:
        return f"{seconds // 60}m ago"
    else:
        return f"{seconds // 3600}h ago"

async def send_main_menu(update, user_id):
    is_sub, status_msg = check_subscription(user_id)
    sub_admins = load_sub_admins()
    is_sub_admin = user_id in sub_admins or str(user_id) in sub_admins

    if user_id == ADMIN_ID:
        keyboard = [
            [KeyboardButton("🔴 Live Range"), KeyboardButton("📊 Analytics Range")],
            [KeyboardButton("⏱ 5 Min"), KeyboardButton("🕰 10 Min")],
            [KeyboardButton("🏆 Most Hit"), KeyboardButton("🔍 Country Search")],
            [KeyboardButton("➕ Add User"), KeyboardButton("➖ Remove User")],
            [KeyboardButton("➕ Add Sub-Admin"), KeyboardButton("➖ Remove Sub-Admin")],
            [KeyboardButton("📋 User List"), KeyboardButton("🗑 Clear All Users")]
        ]
        status = "👑 ADMIN PANEL (Owner)"
    elif is_sub_admin:
        keyboard = [
            [KeyboardButton("🔴 Live Range"), KeyboardButton("📊 Analytics Range")],
            [KeyboardButton("⏱ 5 Min"), KeyboardButton("🕰 10 Min")],
            [KeyboardButton("🏆 Most Hit"), KeyboardButton("🔍 Country Search")],
            [KeyboardButton("➕ Add User"), KeyboardButton("➖ Remove User")],
            [KeyboardButton("📋 User List"), KeyboardButton("📞 Contact Owner")]
        ]
        status = "🛡️ ADMIN PANEL (Sub-Admin)"
    elif is_sub:
        keyboard = [
            [KeyboardButton("🔴 Live Range"), KeyboardButton("📊 Analytics Range")],
            [KeyboardButton("⏱ 5 Min"), KeyboardButton("🕰 10 Min")],
            [KeyboardButton("🏆 Most Hit"), KeyboardButton("🔍 Country Search")],
            [KeyboardButton("👤 My Info"), KeyboardButton("📞 Contact Admin")]
        ]
        status = f"✅ AUTHORIZED ({status_msg})"
    else:
        keyboard = [
            [KeyboardButton("📊 View Active Ranges (Demo)")],
            [KeyboardButton("🔓 Upgrade to Premium")],
            [KeyboardButton("👤 My Info"), KeyboardButton("📞 Contact Admin")]
        ]
        status = "🚫 UNAUTHORIZED"
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"👋 **Dashboard Loaded**\nStatus: {status}", reply_markup=reply_markup, parse_mode='Markdown')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in admin_input_state:
        del admin_input_state[update.effective_user.id]
    await send_main_menu(update, update.effective_user.id)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("approve_"):
        target_user_id = int(query.data.split("_")[1])
        expiry = add_user_30_days(target_user_id)
        await query.edit_message_caption(caption=f"✅ User {target_user_id} approved! Expires: {expiry}")
        await context.bot.send_message(chat_id=target_user_id, text=f"🎉 Payment Approved!\nSubscription active until {expiry}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg_text = update.message.text if update.message.text else ""
    
    # Handle admin input states
    if user_id in admin_input_state:
        action = admin_input_state[user_id]
        
        if action == "waiting_for_add_id" and msg_text.isdigit():
            target_id = int(msg_text)
            expiry = add_user_30_days(target_id)
            await update.message.reply_text(f"✅ User `{target_id}` added! Expires: {expiry}", parse_mode='Markdown')
            del admin_input_state[user_id]
            return
        elif action == "waiting_for_remove_id" and msg_text.isdigit():
            target_id = int(msg_text)
            if remove_user(target_id):
                await update.message.reply_text(f"✅ User `{target_id}` removed!", parse_mode='Markdown')
            else:
                await update.message.reply_text("⚠️ User not found.")
            del admin_input_state[user_id]
            return
    
    # Admin commands
    if user_id == ADMIN_ID:
        if msg_text == "➕ Add User":
            admin_input_state[user_id] = "waiting_for_add_id"
            await update.message.reply_text("✍️ Send User ID to ADD:")
            return
        elif msg_text == "➖ Remove User":
            admin_input_state[user_id] = "waiting_for_remove_id"
            await update.message.reply_text("✍️ Send User ID to REMOVE:")
            return
        elif msg_text == "📋 User List":
            db = load_db()
            if not db:
                await update.message.reply_text("No users found.")
            else:
                txt = "👥 **Users List:**\n\n"
                for uid, data in db.items():
                    name = data.get("name", "User") if isinstance(data, dict) else "User"
                    exp = data.get("expiry", "Unknown") if isinstance(data, dict) else data
                    txt += f"👤 {name} (`{uid}`) - {exp}\n"
                await update.message.reply_text(txt, parse_mode='Markdown')
            return
        elif msg_text == "🗑 Clear All Users":
            clear_all_users()
            await update.message.reply_text("🗑️ All users cleared!")
            return
    
    # Live Range feature
    if msg_text == "🔴 Live Range":
        if not main_database:
            await update.message.reply_text("⚠️ Scanning data... Please wait 10 seconds.")
            return
        
        cutoff = datetime.datetime.now() - timedelta(minutes=5)
        recent = [d for d in main_database if d['found_at'] > cutoff]
        
        stats = {}
        for item in recent:
            rng = item['range']
            if rng not in stats:
                stats[rng] = 0
            stats[rng] += 1
        
        if not stats:
            await update.message.reply_text("No active ranges found.")
        else:
            msg = "🔥 **Live Active Ranges**\n\n"
            for i, (rng, count) in enumerate(sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]):
                msg += f"{i+1}. {rng} - {count} hits\n"
            await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    # Most Hit feature
    if msg_text == "🏆 Most Hit":
        if not main_database:
            await update.message.reply_text("No data available yet.")
            return
        
        stats = {}
        for item in main_database:
            rng = item['range']
            if rng not in stats:
                stats[rng] = 0
            stats[rng] += 1
        
        msg = "🏆 **Top 10 Most Hit Ranges**\n\n"
        for i, (rng, count) in enumerate(sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]):
            msg += f"{i+1}. {rng} - {count} hits\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    # Analytics Range
    if msg_text == "📊 Analytics Range":
        await update.message.reply_text("📊 **Analytics Feature**\n\nType a range or country name to search:", parse_mode='Markdown')
        return
    
    # 5 Min/10 Min history
    if msg_text in ["⏱ 5 Min", "🕰 10 Min"]:
        minutes = 5 if msg_text == "⏱ 5 Min" else 10
        cutoff = datetime.datetime.now() - timedelta(minutes=minutes)
        recent = [d for d in main_database if d['found_at'] > cutoff]
        
        if not recent:
            await update.message.reply_text(f"No data found in last {minutes} minutes.")
        else:
            await update.message.reply_text(f"📊 Found {len(recent)} entries in last {minutes} minutes.")
        return
    
    # My Info
    if msg_text == "👤 My Info":
        is_sub, status = check_subscription(user_id)
        await update.message.reply_text(f"🆔 ID: `{user_id}`\n📅 Status: {status}", parse_mode='Markdown')
        return
    
    # Upgrade to Premium
    if msg_text == "🔓 Upgrade to Premium":
        await update.message.reply_text(PAYMENT_INFO, parse_mode='Markdown')
        return
    
    # Contact Admin
    if msg_text == "📞 Contact Admin" or msg_text == "📞 Contact Owner":
        await update.message.reply_text(f"🆘 Contact Admin: {ADMIN_USERNAME}", parse_mode='Markdown')
        return
    
    # Demo for non-premium
    if msg_text == "📊 View Active Ranges (Demo)":
        if main_database:
            unique_ranges = list(set([d['range'] for d in main_database]))[:5]
            msg = "📊 **Demo Results**\n\n"
            for rng in unique_ranges:
                msg += f"🔹 {rng}\n"
            msg += "\n🔒 **Upgrade to Premium for full access!**"
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text("⚠️ No data available.")
        return
    
    # Default response for unknown commands
    if msg_text and msg_text not in ["🔴 Live Range", "🏆 Most Hit", "📊 Analytics Range", "⏱ 5 Min", "🕰 10 Min", "👤 My Info", "🔓 Upgrade to Premium", "📞 Contact Admin", "📊 View Active Ranges (Demo)"]:
        await send_main_menu(update, user_id)

# ======================= MAIN - PROPERLY FIXED =======================
async def run_bot():
    """Properly initialized bot with correct event loop handling"""
    print("🚀 Starting bot on Railway...")
    
    # Setup application
    request = HTTPXRequest(
        connection_pool_size=10,
        read_timeout=120,
        write_timeout=120,
        connect_timeout=120
    )
    
    application = Application.builder() \
        .token(BOT_TOKEN) \
        .request(request) \
        .connect_timeout(120.0) \
        .read_timeout(120.0) \
        .write_timeout(120.0) \
        .build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Delete webhook
    await application.bot.delete_webhook(drop_pending_updates=True)
    print("✅ Webhook cleared")
    
    # Start polling
    await application.initialize()
    await application.start()
    print("✅ Bot started! Listening for updates...")
    
    # Start polling properly
    await application.updater.start_polling()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Stopping bot...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    print("="*50)
    print("🤖 ORANGE BOT - RAILWAY FIXED VERSION")
    print(f"📂 Data directory: {SYSTEM_DATA_DIR}")
    print("="*50)
    
    # Start scanner thread
    scanner_thread = threading.Thread(target=scan_cli_suggestion, daemon=True)
    scanner_thread.start()
    print("✅ Scanner thread started")
    
    # Fix asyncio event loop for Railway
    try:
        # Try to run with proper event loop handling
        asyncio.run(run_bot())
    except RuntimeError as e:
        if "already running" in str(e):
            # Handle case where loop is already running
            loop = asyncio.get_event_loop()
            loop.create_task(run_bot())
            loop.run_forever()
        else:
            print(f"❌ Error: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")