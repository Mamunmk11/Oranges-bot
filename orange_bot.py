#!/usr/bin/env python3
import sys
import os

# Force stdout to be unbuffered (Railway/Render এ লগ দেখার জন্য)
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

print("="*60)
print("🤖 ORANGE CARRIER BOT STARTING...")
print("="*60)
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print("="*60)

import requests
import time
import datetime
from datetime import timedelta
import re
import threading
import random
import asyncio
import json
import shutil
import html
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
# Telegram imports
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from telegram.request import HTTPXRequest
import platform

print("✅ All imports successful!")

# ======================= ENVIRONMENT DETECTION =======================
IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT') is not None or os.environ.get('RENDER') is not None
print(f"🚀 Running on Railway/Render: {IS_RAILWAY}")

# ======================= ORANGE LOGIN CREDENTIALS =======================
ORANGE_EMAIL = "mamun.mkk100@gmail.com"
ORANGE_PASSWORD = "Ranakhan11325"
print(f"📧 Email configured: {ORANGE_EMAIL[:5]}...")

# ======================= CONFIGURATION =======================
BOT_TOKEN = "8745794978:AAG_1qbHtf6umupdJnTorFI_W63Jr3K6VU8"
ADMIN_ID = 948283424
ADMIN_USERNAME = "@Rana1132"
print(f"🤖 Bot Token: {BOT_TOKEN[:10]}...")
print(f"👑 Admin ID: {ADMIN_ID}")

# 🔥 DATA STORAGE
SYSTEM_DATA_DIR = os.path.join(os.path.expanduser("~"), "orange_bot_data")
if not os.path.exists(SYSTEM_DATA_DIR):
    os.makedirs(SYSTEM_DATA_DIR)
    print(f"📁 Created data directory: {SYSTEM_DATA_DIR}")
else:
    print(f"📁 Data directory exists: {SYSTEM_DATA_DIR}")

USER_DB_FILE = os.path.join(SYSTEM_DATA_DIR, "subscription_db.json")
SUB_ADMIN_FILE = os.path.join(SYSTEM_DATA_DIR, "sub_admins.json")

# PAYMENT MESSAGE
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

👇 **Click below after payment:**
"""

# TRACKING VARIABLES
admin_input_state = {}
user_payment_state = {}
user_payment_data = {}
user_analytics_state = {}
db_lock = threading.Lock()

print("✅ Configuration loaded!")

# ======================= DATABASE SYSTEM =======================
def load_db():
    with db_lock:
        if not os.path.exists(USER_DB_FILE):
            print("ℹ️ First run or DB not found. Starting fresh DB.")
            return {}
        try:
            with open(USER_DB_FILE, "r") as f:
                content = f.read().strip()
                if not content: return {}
                return json.loads(content)
        except:
            backup = USER_DB_FILE + ".bak"
            if os.path.exists(backup):
                shutil.copy(backup, USER_DB_FILE)
                with open(USER_DB_FILE, "r") as f: return json.load(f)
            return {}

def save_db(data):
    with db_lock:
        try:
            if os.path.exists(USER_DB_FILE):
                shutil.copy(USER_DB_FILE, USER_DB_FILE + ".bak")
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
    except: return []

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
    if user_id == ADMIN_ID: return True, "Lifetime (Owner)"
    
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
                print(f"🗑️ Expired User Removed: {user_id}")
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

print("✅ Database functions loaded!")

# ======================= SCANNER SETUP =======================
TARGET_LIST = [
    "Kuwait", "519", "5731", "8801", "8210", "4474", "Bangladesh", "India", "Pakistan",
    "1315", "1425", "1520", "1646", "2011", "2278", "2332", "2626", "2917", "3247",
    "3365", "3375", "3376", "3378", "3462", "3511", "3516", "3598", "3706", "3737",
    "3932", "3933", "3937", "4076", "4473", "4478", "4479", "4822", "4845", "4857",
    "4873", "4878", "4915", "4968", "4983", "5324", "5591", "5715", "5730", "5732",
    "7708", "7863", "8613", "8615", "8617", "8618", "8619", "9178", "9639", "9890",
    "9899", "9981", "9989", "48459"
]

main_database = []            
driver = None
current_country_index = 0 

print(f"✅ Target list loaded: {len(TARGET_LIST)} targets")

# ======================= CHROME BROWSER SETUP =======================
def start_browser():
    global driver
    print("🚀 Starting Chrome browser...")
    options = Options()
    
    if IS_RAILWAY:
        print("🖥️ Running on Railway/Render - Headless mode")
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-setuid-sandbox')
        options.binary_location = "/usr/bin/google-chrome"
        
        try:
            service = Service(executable_path="/usr/local/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=options)
            print("✅ Chrome browser launched on Railway!")
            return True
        except Exception as e:
            print(f"❌ Chrome launch failed: {e}")
            driver = None
            return False
    else:
        print("💻 Running on Local PC")
        options.add_argument('--start-maximized')
        chromedriver_path = r"C:\Users\mamun\Desktop\chromedriver.exe"
        if os.path.exists(chromedriver_path):
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
            print("✅ Chrome browser launched on Local PC!")
            return True
        else:
            print(f"❌ ChromeDriver not found at: {chromedriver_path}")
            driver = None
            return False

def human_type(element, text):
    try:
        driver.execute_script("arguments[0].value = '';", element)
        for char in text: 
            element.send_keys(char)
            time.sleep(random.uniform(0.01, 0.03))
    except: pass

def auto_login_orange():
    global driver
    try:
        print("🔐 Attempting auto-login to Orange Carrier...")
        time.sleep(3)
        
        driver.get("https://www.orangecarrier.com/login")
        print("📍 Navigated to login page")
        time.sleep(5)
        
        # Email field
        try:
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[name='username']"))
            )
            email_field.clear()
            email_field.send_keys(ORANGE_EMAIL)
            print("✅ Email entered")
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Email field not found: {e}")
            return False
        
        # Password field
        try:
            password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password']")
            password_field.clear()
            password_field.send_keys(ORANGE_PASSWORD)
            print("✅ Password entered")
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Password field not found: {e}")
            return False
        
        # Login button
        try:
            login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_btn.click()
            print("✅ Login button clicked")
            time.sleep(8)
            return True
        except Exception as e:
            print(f"⚠️ Login button not found: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Auto-login failed: {e}")
        return False

def scan_cli_suggestion():
    global main_database, current_country_index, driver
    
    print("🔄 Scanner thread started!")
    
    if driver is None: 
        print("📡 Starting browser...")
        if not start_browser():
            print("❌ Browser failed to start!")
            return
    
    print("🔐 Attempting login...")
    if not auto_login_orange():
        print("❌ Login failed!")
        return
    
    print("✅ Login successful!")
    print("🚀 Scanner Logic Started...")
    
    while True:
        try:
            driver.get("https://www.orangecarrier.com/services/cli/access")
            time.sleep(3)
            
            if current_country_index >= len(TARGET_LIST): 
                current_country_index = 0
            target = TARGET_LIST[current_country_index]
            print(f"🔍 Scanning: {target}")
            
            try:
                search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "CLI")))
                search_box.clear()
                search_box.send_keys(target)
                
                search_btn = driver.find_element(By.ID, "SearchBtn")
                search_btn.click()
                time.sleep(2)
                
                current_country_index += 1
                print(f"✅ Scan complete for {target}")
                
            except Exception as e:
                print(f"Scan Error: {e}")
                driver.refresh()
                time.sleep(2)
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Browser Issue: {e}")
            try: 
                driver.quit()
            except: 
                pass
            driver = None
            start_browser()
            time.sleep(5)

print("✅ Scanner function defined!")

# ======================= TELEGRAM BOT LOGIC =======================
def get_time_ago_str(found_time):
    diff = datetime.datetime.now() - found_time
    seconds = int(diff.total_seconds())
    if seconds < 60: 
        return f"{seconds}s ago"
    else: 
        return f"{seconds // 60}m ago"

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
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    try:
        if user_id == ADMIN_ID or is_sub_admin or is_sub:
            await update.message.reply_text(f"👋 **Dashboard Loaded**\nStatus: {status}", reply_markup=reply_markup, parse_mode='Markdown')
        else:
            escaped_username = ADMIN_USERNAME.replace("_", "\\_")
            await update.message.reply_text(f"🚫 **Access Denied!**\nContact: {escaped_username}\n\n🆔 **Your ID:** `{user_id}`", reply_markup=reply_markup, parse_mode='Markdown')
    except: 
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📨 Start command from user: {update.effective_user.id}")
    if update.effective_user.id in admin_input_state:
        del admin_input_state[update.effective_user.id]
    await send_main_menu(update, update.effective_user.id)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg_text = update.message.text.strip() if update.message.text else ""
    print(f"📨 Message from {user_id}: {msg_text[:50]}")
    
    is_sub, status_msg = check_subscription(user_id)
    sub_admins = load_sub_admins()
    is_sub_admin = user_id in sub_admins or str(user_id) in sub_admins

    # Simple response for testing
    if msg_text == "🔴 Live Range":
        await update.message.reply_text(f"📡 Live Ranges Found: {len(main_database)}")
    elif msg_text == "👤 My Info":
        await update.message.reply_text(f"🆔 ID: {user_id}\n📅 Status: {status_msg}")
    else:
        await send_main_menu(update, user_id)

print("✅ Telegram handlers defined!")

# ======================= MAIN EXECUTION =======================
if __name__ == "__main__":
    print("="*60)
    print("🤖 ORANGE CARRIER BOT - MAIN START")
    print("="*60)
    
    # Start scanner in background thread
    print("\n🔄 Starting scanner thread...")
    scanner_thread = threading.Thread(target=scan_cli_suggestion, daemon=True)
    scanner_thread.start()
    print("✅ Scanner thread started")
    
    # Wait a bit for scanner to initialize
    time.sleep(2)
    
    # Setup Telegram bot
    print("\n🤖 Starting Telegram bot...")
    request = HTTPXRequest(
        connection_pool_size=10, 
        read_timeout=60, 
        write_timeout=60, 
        connect_timeout=60,
        http_version="1.1"
    )
    
    app = ApplicationBuilder().token(BOT_TOKEN).request(request).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 Bot is now running and monitoring...")
    print("="*60)
    print("💡 Check Telegram: @Rana1132")
    print("="*60)
    
    try:
        app.run_polling()
    except Exception as e:
        print(f"\n❌ CONNECTION FAILED: {e}")
        import traceback
        traceback.print_exc()
        time.sleep(10)