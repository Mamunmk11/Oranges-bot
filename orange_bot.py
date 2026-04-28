#!/usr/bin/env python3
# Railway Optimized Orange Bot

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
import platform
import hashlib
import logging

# Railway headless setup
os.environ['MOZ_HEADLESS'] = '1'
os.environ['PYTHONUNBUFFERED'] = '1'

from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Telegram imports
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from telegram.request import HTTPXRequest

# ======================= CONFIGURATION =======================
ORANGE_EMAIL = "mamun.mkk100@gmail.com"
ORANGE_PASSWORD = "Ranakhan11325"
BOT_TOKEN = "8745794978:AAG_1qbHtf6umupdJnTorFI_W63Jr3K6VU8"
ADMIN_ID = 948283424
ADMIN_USERNAME = "@Rana1132"

# Railway persistent storage
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
    "Kuwait", "519", "5731", "8210", "4474", "Colombia", "Brazil", "Mexico"
]
main_database = []
driver = None
current_country_index = 0

def setup_railway_browser():
    """Setup browser for Railway environment"""
    global driver
    
    print("🚀 Setting up browser for Railway...")
    
    # Try Firefox first
    try:
        options = FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        driver.set_page_load_timeout(30)
        print("✅ Firefox browser ready on Railway!")
        return driver
    except Exception as e:
        print(f"⚠️ Firefox failed: {e}")
    
    # Try Chrome as fallback
    try:
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        print("✅ Chrome browser ready on Railway!")
        return driver
    except Exception as e:
        print(f"❌ Browser setup failed: {e}")
        return None

def scan_cli_suggestion():
    global main_database, current_country_index, driver
    
    print("🔄 Scanner thread started...")
    
    while True:
        try:
            if driver is None:
                driver = setup_railway_browser()
                if driver is None:
                    print("⚠️ Browser not available, retrying in 30 seconds...")
                    time.sleep(30)
                    continue
            
            # Navigate to Orange Carrier
            try:
                driver.get("https://www.orangecarrier.com/services/cli/access")
                time.sleep(3)
            except Exception as e:
                print(f"⚠️ Navigation error: {e}")
                driver = None
                time.sleep(10)
                continue
            
            # Cycle through targets
            if current_country_index >= len(TARGET_LIST):
                current_country_index = 0
            
            target = TARGET_LIST[current_country_index]
            print(f"🔍 Scanning: {target}")
            
            try:
                # Find and fill search box
                search_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "CLI"))
                )
                search_box.clear()
                search_box.send_keys(target)
                time.sleep(1)
                
                # Click search button
                search_btn = driver.find_element(By.ID, "SearchBtn")
                driver.execute_script("arguments[0].click();", search_btn)
                time.sleep(3)
                
                # Get results
                rows = driver.find_elements(By.XPATH, "//div[@id='Result']//table/tbody/tr")
                found_count = 0
                current_time = datetime.datetime.now()
                
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) > 5:
                        main_database.append({
                            'range': cols[0].text.strip(),
                            'cli': cols[3].text.strip(),
                            'found_at': current_time,
                            'country': target
                        })
                        found_count += 1
                
                print(f"✅ Found {found_count} ranges for {target}")
                current_country_index += 1
                time.sleep(1)
                
                # Clean old data
                cleanup_time = datetime.datetime.now() - timedelta(minutes=30)
                main_database = [d for d in main_database if d['found_at'] > cleanup_time]
                
            except Exception as e:
                print(f"⚠️ Scan error for {target}: {e}")
                current_country_index += 1
                time.sleep(2)
                
        except Exception as e:
            print(f"❌ Scanner error: {e}")
            time.sleep(10)

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
    elif is_sub_admin:
        keyboard = [
            [KeyboardButton("🔴 Live Range"), KeyboardButton("📊 Analytics Range")],
            [KeyboardButton("⏱ 5 Min"), KeyboardButton("🕰 10 Min")],
            [KeyboardButton("🏆 Most Hit"), KeyboardButton("🔍 Country Search")],
            [KeyboardButton("➕ Add User"), KeyboardButton("➖ Remove User")],
            [KeyboardButton("📋 User List"), KeyboardButton("📞 Contact Owner")]
        ]
    elif is_sub:
        keyboard = [
            [KeyboardButton("🔴 Live Range"), KeyboardButton("📊 Analytics Range")],
            [KeyboardButton("⏱ 5 Min"), KeyboardButton("🕰 10 Min")],
            [KeyboardButton("🏆 Most Hit"), KeyboardButton("🔍 Country Search")],
            [KeyboardButton("👤 My Info"), KeyboardButton("📞 Contact Admin")]
        ]
    else:
        keyboard = [
            [KeyboardButton("📊 View Active Ranges (Demo)")],
            [KeyboardButton("🔓 Upgrade to Premium")],
            [KeyboardButton("👤 My Info"), KeyboardButton("📞 Contact Admin")]
        ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 Welcome!", reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_main_menu(update, update.effective_user.id)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("approve_"):
        target_user_id = int(query.data.split("_")[1])
        expiry = add_user_30_days(target_user_id)
        await query.edit_message_caption(
            caption=f"✅ User {target_user_id} approved! Expires: {expiry}"
        )
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"🎉 Payment Approved!\nYour subscription is active until {expiry}"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg_text = update.message.text
    
    # Simple response for now
    await update.message.reply_text(f"Bot is running on Railway!\nYour ID: {user_id}\nCommand: {msg_text}")

# ======================= MAIN =======================
async def main():
    """Main function with proper webhook handling"""
    print("🚀 Starting bot on Railway...")
    
    # CRITICAL FIX: Properly await delete_webhook
    await app.bot.delete_webhook(drop_pending_updates=True)
    print("✅ Webhook cleared")
    
    # Start polling
    await app.run_polling()

if __name__ == "__main__":
    print("="*50)
    print("🤖 ORANGE BOT - RAILWAY DEPLOYMENT")
    print(f"📂 Data directory: {SYSTEM_DATA_DIR}")
    print("="*50)
    
    # Setup request
    request = HTTPXRequest(
        connection_pool_size=10,
        read_timeout=120,
        write_timeout=120,
        connect_timeout=120
    )
    
    # Build application
    app = ApplicationBuilder().token(BOT_TOKEN).request(request).build()
    
    # Start scanner thread
    scanner_thread = threading.Thread(target=scan_cli_suggestion, daemon=True)
    scanner_thread.start()
    print("✅ Scanner thread started")
    time.sleep(3)
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))
    
    # Run bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot stopped")
    except Exception as e:
        print(f"❌ Fatal error: {e}")