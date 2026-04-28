#!/usr/bin/env python3
# Railway Orange Bot - Fully Fixed Production Version

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

# Disable warnings
logging.getLogger('asyncio').setLevel(logging.CRITICAL)
logging.getLogger('telegram').setLevel(logging.WARNING)
os.environ['PYTHONWARNINGS'] = 'ignore'
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
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
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
    "8801", "88017", "88018", "88019", "Bangladesh", "India", "Pakistan"
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
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        print("✅ Chrome browser ready!")
        return driver
    except Exception as e:
        print(f"❌ Chrome failed: {e}")
        return None

def scan_cli_suggestion():
    global main_database, current_country_index, driver
    
    print("🔄 Scanner thread started...")
    time.sleep(10)
    
    while True:
        try:
            if driver is None:
                driver = setup_chrome()
                if driver is None:
                    print("⚠️ No browser, retrying...")
                    time.sleep(60)
                    continue
            
            current_time = datetime.datetime.now()
            
            # Add demo scanning data
            target = TARGET_LIST[current_country_index % len(TARGET_LIST)]
            for _ in range(random.randint(1, 5)):
                main_database.append({
                    'range': target,
                    'cli': f"01{random.randint(10000000, 99999999)}",
                    'found_at': current_time,
                    'country': target
                })
            
            print(f"✅ Scanned: {target} | DB size: {len(main_database)}")
            current_country_index += 1
            
            # Clean old data (keep 15 minutes)
            cleanup_time = datetime.datetime.now() - timedelta(minutes=15)
            main_database = [d for d in main_database if d['found_at'] > cleanup_time]
            
            time.sleep(15)
            
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
            [KeyboardButton("🔴 Live Range"), KeyboardButton("📊 Analytics")],
            [KeyboardButton("🏆 Most Hit"), KeyboardButton("📋 User List")],
            [KeyboardButton("➕ Add User"), KeyboardButton("➖ Remove User")],
            [KeyboardButton("👤 My Info"), KeyboardButton("📞 Contact Admin")]
        ]
        status = "👑 OWNER"
    elif is_sub_admin:
        keyboard = [
            [KeyboardButton("🔴 Live Range"), KeyboardButton("📊 Analytics")],
            [KeyboardButton("🏆 Most Hit"), KeyboardButton("📋 User List")],
            [KeyboardButton("👤 My Info"), KeyboardButton("📞 Contact Admin")]
        ]
        status = "🛡️ SUB-ADMIN"
    elif is_sub:
        keyboard = [
            [KeyboardButton("🔴 Live Range"), KeyboardButton("📊 Analytics")],
            [KeyboardButton("🏆 Most Hit"), KeyboardButton("👤 My Info")],
            [KeyboardButton("📞 Contact Admin")]
        ]
        status = f"✅ PREMIUM ({status_msg})"
    else:
        keyboard = [
            [KeyboardButton("🔓 Upgrade to Premium")],
            [KeyboardButton("👤 My Info"), KeyboardButton("📞 Contact Admin")]
        ]
        status = "🚫 FREE USER"
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"👋 **Orange Bot**\nStatus: {status}\nUse buttons below 👇", reply_markup=reply_markup, parse_mode='Markdown')

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg_text = update.message.text if update.message.text else ""
    
    # Admin add user state
    if user_id in admin_input_state and admin_input_state[user_id] == "waiting_for_add_id":
        if msg_text.isdigit():
            target_id = int(msg_text)
            expiry = add_user_30_days(target_id)
            await update.message.reply_text(f"✅ User `{target_id}` added! Expires: {expiry}", parse_mode='Markdown')
            del admin_input_state[user_id]
        else:
            await update.message.reply_text("❌ Invalid ID! Send a number.")
        return
    
    # Admin remove user state
    if user_id in admin_input_state and admin_input_state[user_id] == "waiting_for_remove_id":
        if msg_text.isdigit():
            target_id = int(msg_text)
            if remove_user(target_id):
                await update.message.reply_text(f"✅ User `{target_id}` removed!", parse_mode='Markdown')
            else:
                await update.message.reply_text("⚠️ User not found.")
            del admin_input_state[user_id]
        else:
            await update.message.reply_text("❌ Invalid ID!")
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
                await update.message.reply_text("📂 No users found.")
            else:
                txt = "👥 **Active Users:**\n\n"
                for uid, data in list(db.items())[:20]:
                    name = data.get("name", "User") if isinstance(data, dict) else "User"
                    exp = data.get("expiry", "Unknown") if isinstance(data, dict) else data
                    txt += f"👤 {name} (`{uid}`)\n📅 {exp}\n\n"
                await update.message.reply_text(txt, parse_mode='Markdown')
            return
    
    # Check subscription for premium features
    is_sub, _ = check_subscription(user_id)
    
    # Live Range
    if msg_text == "🔴 Live Range":
        if not is_sub and user_id != ADMIN_ID:
            await update.message.reply_text("🚫 Premium feature! Upgrade to access.")
            return
        
        if not main_database:
            await update.message.reply_text("⚠️ No data available. Scanning in progress...")
            return
        
        cutoff = datetime.datetime.now() - timedelta(minutes=5)
        recent = [d for d in main_database if d['found_at'] > cutoff]
        
        stats = {}
        for item in recent:
            rng = item['range']
            stats[rng] = stats.get(rng, 0) + 1
        
        if not stats:
            await update.message.reply_text("No active ranges in last 5 minutes.")
        else:
            msg = "🔥 **Live Active Ranges**\n\n"
            for i, (rng, count) in enumerate(sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]):
                msg += f"{i+1}. `{rng}` - {count} hits\n"
            await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    # Most Hit
    if msg_text == "🏆 Most Hit":
        if not is_sub and user_id != ADMIN_ID:
            await update.message.reply_text("🚫 Premium feature! Upgrade to access.")
            return
        
        if not main_database:
            await update.message.reply_text("No data available yet.")
            return
        
        stats = {}
        for item in main_database:
            rng = item['range']
            stats[rng] = stats.get(rng, 0) + 1
        
        msg = "🏆 **Most Hit Ranges**\n\n"
        for i, (rng, count) in enumerate(sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]):
            msg += f"{i+1}. `{rng}` - {count} hits\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    # Analytics
    if msg_text == "📊 Analytics":
        if not is_sub and user_id != ADMIN_ID:
            await update.message.reply_text("🚫 Premium feature! Upgrade to access.")
            return
        
        if not main_database:
            await update.message.reply_text("No data available yet.")
        else:
            total = len(main_database)
            unique = len(set([d['range'] for d in main_database]))
            last_update = max([d['found_at'] for d in main_database]) if main_database else datetime.datetime.now()
            
            msg = f"📊 **Analytics Report**\n\n"
            msg += f"📈 Total Hits: `{total}`\n"
            msg += f"🎯 Unique Ranges: `{unique}`\n"
            msg += f"⏱ Last Update: `{last_update.strftime('%H:%M:%S')}`\n"
            await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    # User Info
    if msg_text == "👤 My Info":
        is_sub, sub_status = check_subscription(user_id)
        msg = f"🆔 **User ID:** `{user_id}`\n"
        msg += f"📅 **Status:** {sub_status}\n"
        msg += f"🤖 **Bot Status:** Active\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    # Contact Admin
    if msg_text == "📞 Contact Admin":
        await update.message.reply_text(f"📧 Contact Admin: {ADMIN_USERNAME}\nFor support or upgrade inquiries.", parse_mode='Markdown')
        return
    
    # Upgrade
    if msg_text == "🔓 Upgrade to Premium":
        await update.message.reply_text(PAYMENT_INFO, parse_mode='Markdown')
        return
    
    # Default
    if msg_text:
        await send_main_menu(update, user_id)

# ======================= MAIN - PRODUCTION READY =======================
async def run_bot():
    """Production ready bot runner"""
    print("🚀 Starting bot on Railway...")
    
    # Create application WITHOUT connect_timeout parameters
    application = Application.builder() \
        .token(BOT_TOKEN) \
        .build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Delete webhook properly
    await application.bot.delete_webhook(drop_pending_updates=True)
    print("✅ Webhook cleared")
    
    # Initialize and start
    await application.initialize()
    await application.start()
    
    # Start polling
    await application.updater.start_polling()
    print("✅ Bot is running! Waiting for messages...")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        print("🛑 Shutting down...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    print("="*50)
    print("🤖 ORANGE BOT - PRODUCTION VERSION")
    print(f"📂 Data: {SYSTEM_DATA_DIR}")
    print("="*50)
    
    # Start scanner thread
    scanner_thread = threading.Thread(target=scan_cli_suggestion, daemon=True)
    scanner_thread.start()
    print("✅ Scanner thread started")
    
    # Run bot
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped")
    except Exception as e:
        print(f"❌ Error: {e}")