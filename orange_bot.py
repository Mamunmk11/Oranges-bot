import requests
import subprocess
import sys
import time
import datetime
from datetime import timedelta
import re
import threading
import random
import os
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
import uuid
import platform
import hashlib

# ======================= ENVIRONMENT DETECTION =======================
IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT') is not None or os.environ.get('RENDER') is not None

# ======================= ORANGE LOGIN CREDENTIALS =======================
ORANGE_EMAIL = "mamun.mkk100@gmail.com"
ORANGE_PASSWORD = "Ranakhan11325"

# ======================= LICENSE CHECK - BYPASSED FOR RAILWAY =======================
# লাইসেন্স চেক সম্পূর্ণ বাইপাস করা হয়েছে
print("🚀 License check bypassed - Running on Cloud Platform")
print(f"📂 Data directory: {os.path.join(os.path.expanduser('~'), 'orange_bot_data')}")

# ======================= CONFIGURATION =======================
BOT_TOKEN = "8745794978:AAG_1qbHtf6umupdJnTorFI_W63Jr3K6VU8"
ADMIN_ID = 948283424
ADMIN_USERNAME = "@Rana1132"

# 🔥 DATA STORAGE
SYSTEM_DATA_DIR = os.path.join(os.path.expanduser("~"), "orange_bot_data")
if not os.path.exists(SYSTEM_DATA_DIR):
    os.makedirs(SYSTEM_DATA_DIR)

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

# ======================= SCANNER SETUP =======================
TARGET_LIST = [
    "Kuwait", "519", "5731", "8801", "8210", "4474", "Colombia", "Brazil", "Mexico", "El Salvador", "Microsoft", "Iran", "Saudi Arabia", 
    "France", "Japan", "Belgium", "Germany", "United Kingdom", "Guinea", "Australia", "China", 
    "Macedonia", "Afghanistan", "Telegram", "Honduras", "Mali", "Morocco", "162", "Togo", 
    "Nigeria", "Philippines", "Zambia", "Guatemala", "821", "India", "Pakistan", "Bangladesh", 
    "UAE", "Qatar", "Egypt", "Indonesia", "Vietnam", "Turkey", "Italy", "Spain", "Russia", 
    "Ukraine", "Kenya", "South Africa", "Ghana", "Sri Lanka", "Nepal", "Iraq", "Jordan", 
    "Oman", "Lebanon", "Ethiopia", "Somalia", "Sudan", "Myanmar", "Cambodia", "Peru", 
    "Dominican Republic", "Malaysia", "Canada", "Argentina", "Chile", "Ecuador", "Venezuela", 
    "Haiti", "Jamaica", "Cuba", "Poland", "Romania", "Netherlands", "Sweden", "Switzerland", 
    "Portugal", "Greece", "Austria", "Czech Republic", "Hungary", "Ireland", "Norway", 
    "Thailand", "Singapore", "South Korea", "Taiwan", "Yemen", "Syria", "Bahrain", "Palestine", 
    "Uzbekistan", "Tajikistan", "Kazakhstan", "Kyrgyzstan", "Zimbabwe", "Uganda", "Tanzania", 
    "Senegal", "Cameroon", "Ivory Coast", "DR Congo", "Algeria", "Tunisia", "Libya", "Benin",
    "Angola", "peru", "519", "9891", "447", "4479", "usa", "telegram 6", "5731", "2519", "5730",
    "8801", "8210", "5255", "5049", "44741", "2348", "9665", "3760", "2519", "9891", "9893", "9659", 
    "5037", "5256", "12133", "5731", "8210", "4077", "5731", "9647", "5731", "9725", "9659", "9160", 
    "9197",
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

# ======================= CHROME BROWSER SETUP (RAILWAY COMPATIBLE) =======================
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
        # Local PC - adjust path as needed
        print("💻 Running on Local PC")
        options.add_argument('--start-maximized')
        chromedriver_path = r"C:\Users\mamun\Desktop\chromedriver.exe"  # Change this path
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
        
        # First, go to login page
        driver.get("https://www.orangecarrier.com/login")
        time.sleep(5)
        
        # Email field
        try:
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[name='username'], #email, #username"))
            )
            email_field.clear()
            for char in ORANGE_EMAIL:
                email_field.send_keys(char)
                time.sleep(random.uniform(0.01, 0.03))
            print("✅ Email entered")
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Email field not found: {e}")
            return False
        
        # Password field
        try:
            password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password'], #password")
            password_field.clear()
            for char in ORANGE_PASSWORD:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.01, 0.03))
            print("✅ Password entered")
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Password field not found: {e}")
            return False
        
        # Login button
        try:
            login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            driver.execute_script("arguments[0].click();", login_btn)
            print("✅ Login button clicked")
            time.sleep(8)
            return True
        except Exception as e:
            print(f"⚠️ Login button not found: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Auto-login failed: {e}")
        return False

def handle_login_process():
    global driver
    login_attempted = False
    
    while True:
        try:
            current_url = driver.current_url
            print(f"📍 Current URL: {current_url}")
            
            if "login" in current_url or "signin" in current_url or "auth" in current_url:
                print("\n🔐 Login page detected!")
                
                if not login_attempted:
                    print("🤖 Attempting auto-login...")
                    if auto_login_orange():
                        print("✅ Auto-login successful! Waiting for redirect...")
                        time.sleep(5)
                        login_attempted = True
                    else:
                        print("⚠️ Auto-login failed! Please check credentials.")
                        print("⏳ Waiting 30 seconds...")
                        time.sleep(30)
                        login_attempted = True
                else:
                    time.sleep(5)
                    
            elif "dashboard" in current_url or "orangecarrier.com" == current_url.rstrip('/'):
                print("✅ Already logged in! Dashboard detected.")
                break
                
            elif "services/cli/access" in current_url:
                print("✅ Access page reached! Ready to scan.")
                break
                
            else:
                time.sleep(2)
                
        except Exception as e:
            print(f"⚠️ Login check error: {e}")
            time.sleep(2)
            
    return True

def scan_cli_suggestion():
    global main_database, current_country_index, driver
    
    if driver is None: 
        if not start_browser():
            print("❌ Browser failed to start!")
            return
    
    if not handle_login_process():
        print("❌ Failed to handle login!")
        return
    
    print("🚀 Scanner Logic Started...")
    
    while True:
        try:
            if "services/cli/access" not in driver.current_url:
                driver.get("https://www.orangecarrier.com/services/cli/access")
                time.sleep(3)
            
            if current_country_index >= len(TARGET_LIST): 
                current_country_index = 0
            target = TARGET_LIST[current_country_index]
            print(f"🔍 Scanning: {target}")
            
            try:
                try: 
                    search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "CLI")))
                except: 
                    driver.refresh()
                    time.sleep(4)
                    continue
                
                human_type(search_box, target)
                search_btn = driver.find_element(By.ID, "SearchBtn")
                driver.execute_script("arguments[0].click();", search_btn)
                
                try: 
                    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//div[@id='Result']//table/tbody/tr")))
                except: 
                    current_country_index += 1
                    continue
                
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
                
                print(f"✅ Found {found_count} ranges in {target}.")
                current_country_index += 1
                time.sleep(1)
            
            except Exception as e:
                print(f"Scan Error: {e}")
                driver.refresh()
                time.sleep(2)
            
            cleanup_time = datetime.datetime.now() - datetime.timedelta(minutes=15)
            main_database = [d for d in main_database if d['found_at'] > cleanup_time]
            
        except Exception as e:
            print(f"Browser Issue: {e}")
            try: 
                driver.quit()
            except: 
                pass
            driver = None
            start_browser()
            time.sleep(5)

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
    if update.effective_user.id in admin_input_state:
        del admin_input_state[update.effective_user.id]
    await send_main_menu(update, update.effective_user.id)

async def auto_refresh_live_data(chat_id, message_id, context):
    for _ in range(60): 
        try:
            await asyncio.sleep(5)
            cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=3)
            relevant_data = [d for d in main_database if d['found_at'] > cutoff_time]
            stats = {}
            for item in relevant_data:
                rng = item['range']
                cli = item['cli']
                seen_time = item['found_at']
                if rng not in stats: 
                    stats[rng] = {'hits': 0, 'clis': set(), 'last_seen': seen_time}
                stats[rng]['hits'] += 1
                stats[rng]['clis'].add(cli)
                if seen_time > stats[rng]['last_seen']: 
                    stats[rng]['last_seen'] = seen_time
            final_list = []
            for rng, data in stats.items():
                if data['hits'] >= 1: 
                    final_list.append({'range': rng, 'hits': data['hits'], 'cli_count': len(data['clis']), 'last_seen': data['last_seen']})
            final_list.sort(key=lambda x: x['hits'], reverse=True)
            top_hits = final_list[:20]
            current_time_str = datetime.datetime.now().strftime("%I:%M:%S %p")
            msg = f"🇧🇩 **Live Active Ranges** (Auto-Update)\n🔄 Updated: {current_time_str}\n\n"
            if not top_hits: 
                msg += "⚠️ **Scanning data...**"
            else:
                for i, item in enumerate(top_hits): 
                    msg += f"**{i+1}. {item['range']}**\n📊 {item['hits']} hits • {item['cli_count']} CLI\n⏱ Last hit: {get_time_ago_str(item['last_seen'])}\n\n"
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=msg, parse_mode='Markdown')
        except: 
            continue

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 
    
    data = query.data
    if data.startswith("approve_"):
        try:
            target_user_id = int(data.split("_")[1])
            expiry = add_user_30_days(target_user_id, name="Member")
            
            original_text = query.message.caption_html if query.message.caption else ""
            if not original_text:
                original_text = html.escape(query.message.caption)

            new_caption = original_text + f"\n\n✅ <b>APPROVED &amp; ADDED</b>\n📅 Expiry: {expiry}"
            await query.edit_message_caption(caption=new_caption, parse_mode='HTML')
            
            welcome_msg = (
                f"🎉 **PAYMENT ACCEPTED!**\n\n"
                f"✅ Your Premium Subscription is now **ACTIVE**!\n"
                f"📅 Valid until: **{expiry}**\n\n"
                f"🚀 You can now access all Live Features."
            )
            try:
                await context.bot.send_message(chat_id=target_user_id, text=welcome_msg, parse_mode='Markdown')
                await context.bot.send_message(chat_id=target_user_id, text="/start")
            except Exception as e:
                print(f"Could not msg user: {e}")
                
        except Exception as e:
            print(f"Error in button_handler: {e}")
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"✅ User {target_user_id} Added manually (Auto-edit failed).")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg_text = update.message.text.strip() if update.message.text else ""
    is_sub, status_msg = check_subscription(user_id)
    
    sub_admins = load_sub_admins()
    is_sub_admin = user_id in sub_admins or str(user_id) in sub_admins

    # ================= 🔥 ANALYTICS LOGIC =================
    if msg_text == "📊 Analytics Range":
        if is_sub or is_sub_admin or user_id == ADMIN_ID:
            user_analytics_state[user_id] = "waiting_for_analytics_input"
            await update.message.reply_text("✍️ **Enter the Range Name or Country:**\nExample: `Kuwait` or `88017`", parse_mode='Markdown')
        else:
            await update.message.reply_text("🚫 Premium Feature Only.")
        return

    if user_id in user_analytics_state and user_analytics_state[user_id] == "waiting_for_analytics_input":
        search_query = msg_text.lower()
        
        filtered_data = [d for d in main_database if search_query in d['range'].lower() or search_query in d['country'].lower()]
        
        if not filtered_data:
            await update.message.reply_text(f"❌ No data found for: **{msg_text}**\nMake sure the bot has scanned this range recently.", parse_mode='Markdown')
        else:
            stats = {}
            for item in filtered_data:
                rng = item['range']
                cli = item['cli']
                if rng not in stats: 
                    stats[rng] = {'hits': 0, 'clis': set(), 'last_seen': item['found_at']}
                
                stats[rng]['hits'] += 1
                stats[rng]['clis'].add(cli)
                
                if item['found_at'] > stats[rng]['last_seen']: 
                    stats[rng]['last_seen'] = item['found_at']
            
            sorted_stats = sorted(stats.items(), key=lambda x: x[1]['hits'], reverse=True)
            top_10 = sorted_stats[:10]
            
            res_msg = f"📊 **ANALYTICS REPORT**\n🔎 Search: `{msg_text}`\n🔥 Highest Hits (Top 10)\n\n"
            for i, (rng, data) in enumerate(top_10):
                res_msg += f"**{i+1}. {rng}**\n🎯 Hits: {data['hits']} | 📞 CLI: {len(data['clis'])}\n⏱ {get_time_ago_str(data['last_seen'])}\n\n"
            
            await update.message.reply_text(res_msg, parse_mode='Markdown')

        del user_analytics_state[user_id]
        return

    # ================= 🔥 ADMIN LOGIC =================
    if user_id == ADMIN_ID or is_sub_admin:
        if msg_text == "➕ Add User":
            admin_input_state[user_id] = "waiting_for_add_id"
            await update.message.reply_text("✍️ **Please type the User ID to ADD:**", parse_mode='Markdown')
            return
        elif msg_text == "➖ Remove User":
            admin_input_state[user_id] = "waiting_for_remove_id"
            await update.message.reply_text("✍️ **Please type the User ID to REMOVE:**", parse_mode='Markdown')
            return
        elif msg_text == "📋 User List":
            db = load_db()
            if not db: 
                await update.message.reply_text("📂 No active users.")
            else:
                txt = "👥 **Active Users List:**\n\n"
                for uid, data in db.items():
                    name = data.get("name", "User") if isinstance(data, dict) else "User"
                    exp = data.get("expiry", "Unknown") if isinstance(data, dict) else data
                    txt += f"👤 <a href='tg://user?id={uid}'>{name}</a> (<code>{uid}</code>)\n📅 Exp: {exp}\n------------------\n"
                await update.message.reply_text(txt, parse_mode='HTML')
            return
        elif msg_text == "🗑 Clear All Users":
            if user_id != ADMIN_ID:
                await update.message.reply_text("🚫 Only Owner can clear all users.")
                return
            clear_all_users()
            await update.message.reply_text("🗑️ **All users deleted!**")
            return

        if user_id == ADMIN_ID:
            if msg_text == "➕ Add Sub-Admin":
                admin_input_state[user_id] = "waiting_for_add_sub_admin"
                await update.message.reply_text("🛡️ **Enter User ID to make SUB-ADMIN:**")
                return
            elif msg_text == "➖ Remove Sub-Admin":
                admin_input_state[user_id] = "waiting_for_remove_sub_admin"
                existing = load_sub_admins()
                await update.message.reply_text(f"🛡️ **Current Sub-Admins:** {existing}\n\n✍️ **Enter ID to Remove:**")
                return

        if user_id in admin_input_state:
            action = admin_input_state[user_id]
            if msg_text.lower() == "cancel": 
                del admin_input_state[user_id]
                await send_main_menu(update, user_id)
                return

            try:
                target_id = int(msg_text)
                if action == "waiting_for_add_id":
                    expiry = add_user_30_days(target_id, name="New Member") 
                    await update.message.reply_text(f"✅ **Success!**\nUser `{target_id}` added.\n📅 Expires: {expiry}", parse_mode='Markdown')
                    try: 
                        welcome_msg = (
                            f"🎉 **Congratulations!**\n\n"
                            f"✅ Your Premium Subscription is now **ACTIVE**!\n"
                            f"📅 Valid until: **{expiry}**\n\n"
                            f"🚀 You can now access all Live Features."
                        )
                        await context.bot.send_message(chat_id=target_id, text=welcome_msg, parse_mode='Markdown')
                        await context.bot.send_message(chat_id=target_id, text="/start")
                    except Exception as e: 
                        await update.message.reply_text(f"⚠️ User added, but could not send DM. Error: {e}")

                elif action == "waiting_for_remove_id":
                    if remove_user(target_id): 
                        await update.message.reply_text(f"✅ User `{target_id}` removed!", parse_mode='Markdown')
                    else: 
                        await update.message.reply_text("⚠️ Not found.")
                
                elif action == "waiting_for_add_sub_admin":
                    current_subs = load_sub_admins()
                    if target_id not in current_subs:
                        current_subs.append(target_id)
                        save_sub_admins(current_subs)
                        await update.message.reply_text(f"✅ **Success!**\nUser `{target_id}` is now a Sub-Admin.", parse_mode='Markdown')
                        try: 
                            await context.bot.send_message(chat_id=target_id, text="🛡️ **You have been promoted to SUB-ADMIN!**\nType /start to see Admin Panel.")
                        except: 
                            pass
                    else:
                        await update.message.reply_text("⚠️ User is already a Sub-Admin.")

                elif action == "waiting_for_remove_sub_admin":
                    current_subs = load_sub_admins()
                    if target_id in current_subs:
                        current_subs.remove(target_id)
                        save_sub_admins(current_subs)
                        await update.message.reply_text(f"✅ User `{target_id}` removed from Sub-Admins.", parse_mode='Markdown')
                    else:
                        await update.message.reply_text("⚠️ ID not found in Sub-Admin list.")
                
                del admin_input_state[user_id]
                return
            except ValueError: 
                await update.message.reply_text("❌ Invalid ID!")
                return

    # ================= 🔥 NORMAL LOGIC =================
    if msg_text == "🔄 Refresh Menu" or msg_text == "🔙 Back": 
        await send_main_menu(update, user_id)
        return
    if msg_text == "👤 My Info": 
        await update.message.reply_text(f"🆔 **ID:** `{user_id}`\n📅 **Status:** {status_msg}", parse_mode='Markdown')
        return
    if msg_text == "📞 Contact Admin" or msg_text == "📞 Contact Owner":
        escaped_username = ADMIN_USERNAME.replace("_", "\\_")
        await update.message.reply_text(f"🆘 **Need Help?**\nDirect Contact: {escaped_username}", parse_mode='Markdown')
        return

    # 🔥 DEMO FEATURE
    if msg_text == "📊 View Active Ranges (Demo)":
        if is_sub:
            await update.message.reply_text("✅ আপনি প্রিমিয়াম মেম্বার! '🔴 Live Range' বাটন ব্যবহার করুন।")
        else:
            if not main_database:
                await update.message.reply_text("⚠️ Scanning data... Please wait 10 seconds.")
            else:
                stats = {}
                for item in main_database:
                    rng = item['range']
                    seen_time = item['found_at']
                    if rng not in stats: 
                        stats[rng] = {'hits': 0, 'last_seen': seen_time}
                    stats[rng]['hits'] += 1
                    if seen_time > stats[rng]['last_seen']: 
                        stats[rng]['last_seen'] = seen_time
                final_demo = []
                for rng, data in stats.items():
                    final_demo.append({'range': rng, 'hits': data['hits'], 'last_seen': data['last_seen']})
                final_demo.sort(key=lambda x: x['hits'], reverse=True)
                top_5_demo = final_demo[:5]
                msg = "🇧🇩 **Live Demo Results (Top 5)**\n\n"
                for i, item in enumerate(top_5_demo):
                    msg += f"**{i+1}. {item['range']}**\n"
                msg += "\n🔒 **সম্পূর্ণ অ্যাক্সেস পেতে প্রিমিয়াম করুন**"
                await update.message.reply_text(msg, parse_mode='Markdown')
        return

    # 🔥 Payment Flow
    if msg_text == "🔓 Upgrade to Premium":
        keyboard = [[KeyboardButton("✅ Submit Payment Proof")], [KeyboardButton("🔙 Back")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(PAYMENT_INFO, reply_markup=reply_markup, parse_mode='Markdown')
        return

    if msg_text == "✅ Submit Payment Proof":
        keyboard = [[KeyboardButton("Bkash/Nagad")], [KeyboardButton("Binance")], [KeyboardButton("🔙 Back")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        user_payment_state[user_id] = "selecting_method"
        await update.message.reply_text("💳 **Select Payment Method:**", reply_markup=reply_markup)
        return

    if user_id in user_payment_state and user_payment_state[user_id] == "selecting_method":
        if msg_text == "Bkash/Nagad" or msg_text == "Binance":
            user_payment_state[user_id] = "waiting_for_proof_ss"
            user_payment_data[user_id] = {"method": msg_text} 
            await update.message.reply_text("📸 **Please send the payment Screenshot (SS):**")
            return
    
    if user_id in user_payment_state and user_payment_state[user_id] == "waiting_for_proof_ss":
        if update.message.photo:
            user_payment_data[user_id]["photo_id"] = update.message.photo[-1].file_id 
            user_payment_state[user_id] = "waiting_for_last_3_digit"
            await update.message.reply_text("🔢 **Now send the Last 3 Digits of your number/transaction:**")
            return
        else:
            await update.message.reply_text("❌ Please send a Photo (Screenshot)!")
            return

    if user_id in user_payment_state and user_payment_state[user_id] == "waiting_for_last_3_digit":
        last_3_digit = msg_text
        stored_data = user_payment_data.get(user_id)
        
        if stored_data:
            method = stored_data["method"]
            photo_id = stored_data["photo_id"]
            
            caption = (
                f"🔔 **NEW PAYMENT REQUEST!**\n"
                f"👤 {update.effective_user.mention_html()} (`{user_id}`)\n"
                f"💳 Method: **{method}**\n"
                f"🔢 Last 3 Digits: `{last_3_digit}`\n\n"
                f"👇 **Action:**"
            )
            
            approve_btn = InlineKeyboardButton(f"✅ Approve & Add {user_id}", callback_data=f"approve_{user_id}")
            admin_markup = InlineKeyboardMarkup([[approve_btn]])

            await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=caption, parse_mode='HTML', reply_markup=admin_markup)
            
            await update.message.reply_text("✅ Submitted Successfully!\nWait for Admin approval.")
            
            del user_payment_state[user_id]
            del user_payment_data[user_id]
            await send_main_menu(update, user_id)
            return

    if not is_sub:
        escaped_username = ADMIN_USERNAME.replace("_", "\\_")
        await update.message.reply_text(f"🚫 **Access Denied!**\nContact: {escaped_username}", parse_mode='Markdown')
        return

    # Authorized Features
    if msg_text == "🔴 Live Range":
        msg = await update.message.reply_text("🔄 **Starting Live Monitor...**", parse_mode='Markdown')
        asyncio.create_task(auto_refresh_live_data(update.message.chat_id, msg.message_id, context))
        return
    
    minutes = 0
    limit = 20
    header_text = ""
    is_custom_search = False
    custom_country_name = ""
    if msg_text == "⏱ 5 Min": 
        minutes = 5
        limit = 40
        header_text = "⏱ **Last 5 Minutes History**"
    elif msg_text == "🕰 10 Min": 
        minutes = 10
        limit = 40
        header_text = "🕰 **Last 10 Minutes History**"
    elif msg_text == "🏆 Most Hit": 
        minutes = 15
        limit = 20
        header_text = "🏆 **Top 20 Most Hit Ranges**"
    elif msg_text == "🔍 Country Search": 
        await update.message.reply_text("✍️ **Type Country Name:**")
        return
    else: 
        is_custom_search = True
        custom_country_name = msg_text
        minutes = 30
        limit = 50
        header_text = f"🌍 **Results for: {custom_country_name.upper()}**"

    cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=minutes)
    if is_custom_search: 
        relevant_data = [d for d in main_database if custom_country_name.lower() in d['country'].lower()]
    else: 
        relevant_data = [d for d in main_database if d['found_at'] > cutoff_time]
    
    stats = {}
    for item in relevant_data:
        rng = item['range']
        cli = item['cli']
        seen_time = item['found_at']
        if rng not in stats: 
            stats[rng] = {'hits': 0, 'clis': set(), 'last_seen': seen_time}
        stats[rng]['hits'] += 1
        stats[rng]['clis'].add(cli)
        if seen_time > stats[rng]['last_seen']: 
            stats[rng]['last_seen'] = seen_time
    final_list = []
    for rng, data in stats.items():
        if data['hits'] >= 1: 
            final_list.append({'range': rng, 'hits': data['hits'], 'cli_count': len(data['clis']), 'last_seen': data['last_seen']})
    final_list.sort(key=lambda x: x['hits'], reverse=True)
    top_hits = final_list[:limit]

    msg = f"{header_text}\n\n"
    if not top_hits: 
        msg += "⚠️ **No data found.**"
    else:
        for i, item in enumerate(top_hits): 
            msg += f"**{i+1}. {item['range']}**\n📊 {item['hits']} hits • {item['cli_count']} CLI\n⏱ Last hit: {get_time_ago_str(item['last_seen'])}\n\n"
    try: 
        await update.message.reply_text(msg, parse_mode='Markdown')
    except: 
        pass

# ======================= MAIN EXECUTION =======================
if __name__ == "__main__":
    print("="*60)
    print("🤖 ORANGE CARRIER BOT - RAILWAY DEPLOYMENT")
    print("="*60)
    print(f"🚀 Running on Railway: {IS_RAILWAY}")
    print(f"📂 Data directory: {SYSTEM_DATA_DIR}")
    print(f"🤖 Bot Token: {BOT_TOKEN[:10]}...")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print("✅ License check: BYPASSED for Railway")
    print("="*60)
    
    # Start scanner in background thread
    print("\n🔄 Starting scanner thread...")
    scanner_thread = threading.Thread(target=scan_cli_suggestion, daemon=True)
    scanner_thread.start()
    print("✅ Scanner thread started")
    
    # Setup Telegram bot with longer timeouts for Railway
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
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & (~filters.COMMAND), handle_message))
    
    print("🚀 Bot is now running and monitoring...")
    print("="*60)
    
    try:
        app.run_polling()
    except Exception as e:
        print(f"\n❌ CONNECTION FAILED: {e}")
        print("💡 Solution: Check your bot token and internet connection")
        time.sleep(10)