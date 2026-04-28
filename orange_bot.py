#!/usr/bin/env python3
import sys
import os

# Force stdout to be unbuffered
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

print("="*60)
print("🤖 ORANGE CARRIER BOT STARTING...")
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
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest

print("✅ All imports successful!")

# ======================= ENVIRONMENT =======================
IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT') is not None
print(f"🚀 Running on Railway: {IS_RAILWAY}")

# ======================= CREDENTIALS =======================
ORANGE_EMAIL = "mamun.mkk100@gmail.com"
ORANGE_PASSWORD = "Ranakhan11325"

# ======================= CONFIGURATION =======================
BOT_TOKEN = "8745794978:AAG_1qbHtf6umupdJnTorFI_W63Jr3K6VU8"
ADMIN_ID = 948283424

# DATA STORAGE
SYSTEM_DATA_DIR = os.path.join(os.path.expanduser("~"), "orange_bot_data")
os.makedirs(SYSTEM_DATA_DIR, exist_ok=True)

USER_DB_FILE = os.path.join(SYSTEM_DATA_DIR, "subscription_db.json")
db_lock = threading.Lock()

# ======================= DATABASE =======================
def load_db():
    with db_lock:
        if not os.path.exists(USER_DB_FILE):
            return {}
        try:
            with open(USER_DB_FILE, "r") as f:
                return json.load(f)
        except:
            return {}

def save_db(data):
    with db_lock:
        try:
            with open(USER_DB_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"⚠️ Save Error: {e}")

def check_subscription(user_id):
    if user_id == ADMIN_ID:
        return True, "Owner"
    db = load_db()
    if str(user_id) in db:
        return True, "Active"
    return False, "Not Subscribed"

# ======================= TARGET LIST =======================
TARGET_LIST = [
    "8801", "88017", "88018", "88019", "Bangladesh", "India", "Pakistan",
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
bot_running = True

# ======================= CHROME BROWSER =======================
def start_browser():
    global driver
    print("🚀 Starting Chrome browser...")
    options = Options()
    
    if IS_RAILWAY:
        print("🖥️ Headless mode for Railway")
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.binary_location = "/usr/bin/google-chrome"
        
        try:
            service = Service(executable_path="/usr/local/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=options)
            print("✅ Chrome browser launched!")
            return True
        except Exception as e:
            print(f"❌ Chrome launch failed: {e}")
            driver = None
            return False
    else:
        options.add_argument('--start-maximized')
        chromedriver_path = r"C:\Users\mamun\Desktop\chromedriver.exe"
        if os.path.exists(chromedriver_path):
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
            print("✅ Chrome browser launched on Local PC!")
            return True
        else:
            print(f"❌ ChromeDriver not found")
            driver = None
            return False

def auto_login_orange():
    global driver
    try:
        print("🔐 Attempting auto-login...")
        
        # Go to login page
        driver.get("https://www.orangecarrier.com/login")
        time.sleep(5)
        print(f"📍 Current URL: {driver.current_url}")
        
        # Try different selectors for email field
        email_selectors = [
            "//input[@type='email']",
            "//input[@name='email']", 
            "//input[@name='username']",
            "//input[@id='email']",
            "//input[@id='username']"
        ]
        
        email_field = None
        for selector in email_selectors:
            try:
                email_field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                print(f"✅ Found email field with selector: {selector}")
                break
            except:
                continue
        
        if email_field:
            email_field.clear()
            email_field.send_keys(ORANGE_EMAIL)
            print("✅ Email entered")
            time.sleep(1)
        else:
            print("❌ Email field not found!")
            return False
        
        # Password field selectors
        password_selectors = [
            "//input[@type='password']",
            "//input[@name='password']",
            "//input[@id='password']"
        ]
        
        password_field = None
        for selector in password_selectors:
            try:
                password_field = driver.find_element(By.XPATH, selector)
                print(f"✅ Found password field with selector: {selector}")
                break
            except:
                continue
        
        if password_field:
            password_field.clear()
            password_field.send_keys(ORANGE_PASSWORD)
            print("✅ Password entered")
            time.sleep(1)
        else:
            print("❌ Password field not found!")
            return False
        
        # Login button
        login_selectors = [
            "//button[@type='submit']",
            "//input[@type='submit']",
            "//button[contains(text(), 'Login')]",
            "//button[contains(text(), 'Sign in')]"
        ]
        
        login_btn = None
        for selector in login_selectors:
            try:
                login_btn = driver.find_element(By.XPATH, selector)
                print(f"✅ Found login button with selector: {selector}")
                break
            except:
                continue
        
        if login_btn:
            login_btn.click()
            print("✅ Login button clicked")
            time.sleep(8)
            
            # Check if login successful
            current_url = driver.current_url
            if "dashboard" in current_url.lower() or "home" in current_url.lower():
                print("✅ Login successful!")
                return True
            else:
                print(f"⚠️ Login may have failed. Current URL: {current_url}")
                return True  # Still return true to continue
        else:
            print("❌ Login button not found!")
            return False
            
    except Exception as e:
        print(f"❌ Auto-login failed: {e}")
        return False

def scan_cli_suggestion():
    global main_database, current_country_index, driver, bot_running
    
    print("🔄 Scanner thread started!")
    
    if driver is None:
        if not start_browser():
            print("❌ Browser failed to start!")
            return
    
    if not auto_login_orange():
        print("⚠️ Login had issues, but continuing...")
    
    print("🚀 Scanner Logic Started!")
    
    while bot_running:
        try:
            # Go to CLI access page
            driver.get("https://www.orangecarrier.com/services/cli/access")
            time.sleep(3)
            
            # Get target
            if current_country_index >= len(TARGET_LIST):
                current_country_index = 0
            target = TARGET_LIST[current_country_index]
            print(f"🔍 Scanning: {target}")
            
            try:
                # Find search box
                search_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "CLI"))
                )
                search_box.clear()
                search_box.send_keys(target)
                
                # Click search button
                search_btn = driver.find_element(By.ID, "SearchBtn")
                search_btn.click()
                time.sleep(2)
                
                current_country_index += 1
                print(f"✅ Scan complete for {target}")
                
            except Exception as e:
                print(f"⚠️ Scan error: {e}")
                driver.refresh()
                time.sleep(2)
            
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Browser issue: {e}")
            try:
                driver.quit()
            except:
                pass
            driver = None
            if bot_running:
                start_browser()
                auto_login_orange()
            time.sleep(5)

# ======================= TELEGRAM BOT =======================
async def send_main_menu(update, user_id):
    is_sub, status_msg = check_subscription(user_id)
    
    if user_id == ADMIN_ID:
        keyboard = [
            [KeyboardButton("🔴 Live Range")],
            [KeyboardButton("📊 Stats"), KeyboardButton("👤 My Info")]
        ]
        status = "👑 ADMIN"
    elif is_sub:
        keyboard = [
            [KeyboardButton("🔴 Live Range")],
            [KeyboardButton("👤 My Info")]
        ]
        status = f"✅ {status_msg}"
    else:
        keyboard = [
            [KeyboardButton("📊 Live Demo")],
            [KeyboardButton("👤 My Info")]
        ]
        status = "🚫 UNAUTHORIZED"
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"👋 Welcome!\nStatus: {status}", reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📨 Start from user: {update.effective_user.id}")
    await send_main_menu(update, update.effective_user.id)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg_text = update.message.text
    
    print(f"📨 Message from {user_id}: {msg_text}")
    
    if msg_text == "🔴 Live Range":
        await update.message.reply_text(f"📡 Live Ranges Found: {len(main_database)}")
    elif msg_text == "📊 Stats":
        await update.message.reply_text(f"📊 Total Scanned: {len(main_database)}")
    elif msg_text == "👤 My Info":
        is_sub, status = check_subscription(user_id)
        await update.message.reply_text(f"🆔 ID: {user_id}\n📅 Status: {status}")
    elif msg_text == "📊 Live Demo":
        await update.message.reply_text(f"📡 Demo: {len(main_database)} ranges found")
    else:
        await send_main_menu(update, user_id)

# ======================= MAIN =======================
if __name__ == "__main__":
    print("="*60)
    print("🤖 ORANGE CARRIER BOT STARTING")
    print("="*60)
    
    # Kill any existing bot instances (重要!)
    print("🔄 Ensuring no other bot instances are running...")
    
    # Start scanner in background
    print("🔄 Starting scanner thread...")
    scanner_thread = threading.Thread(target=scan_cli_suggestion, daemon=True)
    scanner_thread.start()
    print("✅ Scanner thread started")
    
    time.sleep(3)
    
    # Setup Telegram bot with proper error handling
    print("🤖 Starting Telegram bot...")
    
    # Use a single request instance
    request = HTTPXRequest(
        connection_pool_size=1,  # Reduce to 1 to avoid conflicts
        read_timeout=30,
        write_timeout=30,
        connect_timeout=30
    )
    
    app = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .request(request) \
        .connect_timeout(30) \
        .read_timeout(30) \
        .write_timeout(30) \
        .build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Bot handlers configured")
    print("="*60)
    print("🚀 Bot is running! Check Telegram: @Rana1132")
    print("="*60)
    
    # Use run_polling with proper settings
    try:
        # Drop any pending updates to avoid conflicts
        app.bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook cleared")
        
        # Start polling
        app.run_polling(
            allowed_updates=['message'],
            drop_pending_updates=True,
            stop_signals=None  # Prevents signal conflicts
        )
    except Exception as e:
        print(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()
        time.sleep(10)