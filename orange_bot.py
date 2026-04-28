#!/usr/bin/env python3
import sys
import os

# Force unbuffered output for Railway logs
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

print("="*60)
print("🤖 ORANGE CARRIER BOT STARTING...")
print("="*60)

# Import required modules
try:
    import requests
    print("✅ requests imported")
except ImportError as e:
    print(f"❌ requests import failed: {e}")
    sys.exit(1)

try:
    import time
    import datetime
    import threading
    import random
    import json
    from datetime import timedelta
    print("✅ core modules imported")
except ImportError as e:
    print(f"❌ core modules import failed: {e}")
    sys.exit(1)

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    print("✅ selenium imported")
except ImportError as e:
    print(f"❌ selenium import failed: {e}")
    sys.exit(1)

try:
    from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
    from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
    from telegram.request import HTTPXRequest
    print("✅ telegram imported")
except ImportError as e:
    print(f"❌ telegram import failed: {e}")
    sys.exit(1)

print("="*60)

# ======================= CONFIGURATION =======================
IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT') is not None
BOT_TOKEN = "8745794978:AAG_1qbHtf6umupdJnTorFI_W63Jr3K6VU8"
ADMIN_ID = 948283424
ORANGE_EMAIL = "mamun.mkk100@gmail.com"
ORANGE_PASSWORD = "Ranakhan11325"

print(f"🚀 Railway mode: {IS_RAILWAY}")
print(f"🤖 Bot Token: {BOT_TOKEN[:10]}...")
print(f"👑 Admin ID: {ADMIN_ID}")

# Data directory
DATA_DIR = os.path.join(os.path.expanduser("~"), "orange_bot_data")
os.makedirs(DATA_DIR, exist_ok=True)
USER_DB_FILE = os.path.join(DATA_DIR, "users.json")
print(f"📁 Data directory: {DATA_DIR}")

# Global variables
driver = None
main_database = []
current_index = 0
bot_running = True

# Target list
TARGET_LIST = [
    "8801", "88017", "88018", "Bangladesh", "India", "Pakistan",
    "1315", "1425", "1520", "1646", "2011", "2278", "2332", "2626",
    "2917", "3247", "3365", "3375", "3376", "3378", "3462", "3511",
    "3516", "3598", "3706", "3737", "3932", "3933", "3937", "4076",
    "4473", "4478", "4479", "4822", "4845", "4857", "4873", "4878",
    "4915", "4968", "4983", "5324", "5591", "5715", "5730", "5732",
    "7708", "7863", "8613", "8615", "8617", "8618", "8619", "9178",
    "9639", "9890", "9899", "9981", "9989", "48459"
]
print(f"✅ {len(TARGET_LIST)} targets loaded")

# ======================= DATABASE FUNCTIONS =======================
def load_users():
    if not os.path.exists(USER_DB_FILE):
        return {}
    try:
        with open(USER_DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    try:
        with open(USER_DB_FILE, 'w') as f:
            json.dump(users, f, indent=4)
    except Exception as e:
        print(f"⚠️ Save error: {e}")

def check_user(user_id):
    if user_id == ADMIN_ID:
        return True
    users = load_users()
    return str(user_id) in users

# ======================= BROWSER FUNCTIONS =======================
def start_browser():
    global driver
    print("🚀 Starting Chrome browser...")
    
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    if IS_RAILWAY:
        options.binary_location = "/usr/bin/google-chrome"
        service = Service(executable_path="/usr/local/bin/chromedriver")
    else:
        # For local Windows
        chromedriver_path = r"C:\Users\mamun\Desktop\chromedriver.exe"
        service = Service(chromedriver_path)
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        print("✅ Chrome browser started!")
        return True
    except Exception as e:
        print(f"❌ Browser failed: {e}")
        driver = None
        return False

def do_login():
    global driver
    try:
        print("🔐 Logging in...")
        driver.get("https://www.orangecarrier.com/login")
        time.sleep(5)
        
        # Try to find email field
        email = driver.find_element(By.CSS_SELECTOR, "input[type='email'], input[name='email']")
        email.clear()
        email.send_keys(ORANGE_EMAIL)
        print("✅ Email entered")
        time.sleep(1)
        
        # Find password field
        password = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password.clear()
        password.send_keys(ORANGE_PASSWORD)
        print("✅ Password entered")
        time.sleep(1)
        
        # Find and click login button
        login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_btn.click()
        print("✅ Login clicked")
        time.sleep(5)
        
        return True
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False

def scanner_loop():
    global driver, main_database, current_index, bot_running
    
    print("🔄 Scanner thread started")
    
    # Start browser and login
    if not start_browser():
        print("❌ Cannot start browser")
        return
    
    if not do_login():
        print("⚠️ Login issue, but continuing...")
    
    print("🚀 Scanner running...")
    
    while bot_running:
        try:
            # Go to CLI page
            driver.get("https://www.orangecarrier.com/services/cli/access")
            time.sleep(3)
            
            # Get target
            target = TARGET_LIST[current_index % len(TARGET_LIST)]
            current_index += 1
            print(f"🔍 Scanning: {target}")
            
            # Find and fill search box
            search = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "CLI"))
            )
            search.clear()
            search.send_keys(target)
            
            # Click search
            btn = driver.find_element(By.ID, "SearchBtn")
            btn.click()
            time.sleep(2)
            
            print(f"✅ Scanned: {target}")
            
        except Exception as e:
            print(f"⚠️ Scan error: {e}")
            time.sleep(5)
            
            # Try to recover
            try:
                driver.refresh()
            except:
                driver = None
                start_browser()
                do_login()
        
        time.sleep(1)

# ======================= TELEGRAM BOT =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print(f"📨 /start from {user_id}")
    
    if user_id == ADMIN_ID or check_user(user_id):
        keyboard = [[KeyboardButton("🔴 Live Range")]]
        reply = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("👋 Welcome to Orange Bot!\nStatus: ✅ PREMIUM", reply_markup=reply)
    else:
        keyboard = [[KeyboardButton("📊 Demo")]]
        reply = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("👋 Welcome!\nStatus: ⚠️ DEMO MODE\nContact @Rana1132 for premium", reply_markup=reply)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    print(f"📨 {user_id}: {text}")
    
    if text == "🔴 Live Range":
        count = len(main_database)
        await update.message.reply_text(f"📡 Live Ranges Found: {count}")
    elif text == "📊 Demo":
        await update.message.reply_text(f"📊 Demo Stats: {len(main_database)} ranges")
    else:
        await update.message.reply_text("Send /start to see menu")

# ======================= MAIN =======================
if __name__ == "__main__":
    print("="*60)
    print("🚀 STARTING BOT...")
    print("="*60)
    
    # Start scanner thread
    print("Starting scanner thread...")
    scan_thread = threading.Thread(target=scanner_loop, daemon=True)
    scan_thread.start()
    print("✅ Scanner thread started")
    
    time.sleep(2)
    
    # Start Telegram bot
    print("Starting Telegram bot...")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("="*60)
    print("✅ BOT IS RUNNING!")
    print("📱 Check: https://t.me/Updateotpnew_bot")
    print("="*60)
    
    # Clear any webhook conflicts
    try:
        app.bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook cleared")
    except:
        pass
    
    # Start polling
    app.run_polling(allowed_updates=['message'], drop_pending_updates=True)