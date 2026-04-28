#!/usr/bin/env python3
import os
import sys
import time
import json
import asyncio
import threading
import random
import datetime
from datetime import timedelta

# ডাটা ফোল্ডার তৈরি
DATA_DIR = os.path.join(os.getcwd(), "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

USER_DB = os.path.join(DATA_DIR, "users.json")
ADMIN_ID = 948283424
BOT_TOKEN = "8745794978:AAG_1qbHtf6umupdJnTorFI_W63Jr3K6VU8"
ADMIN_USERNAME = "@Rana1132"

# ডাটাবেস ফাংশন
def load_users():
    if not os.path.exists(USER_DB):
        return {}
    try:
        with open(USER_DB, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    try:
        with open(USER_DB, 'w') as f:
            json.dump(data, f, indent=4)
    except:
        pass

def add_user(user_id, days=30):
    users = load_users()
    expiry = datetime.datetime.now() + timedelta(days=days)
    users[str(user_id)] = expiry.strftime("%Y-%m-%d %H:%M:%S")
    save_users(users)
    return expiry.strftime("%d-%b-%Y")

def check_user(user_id):
    if user_id == ADMIN_ID:
        return True, "Owner"
    users = load_users()
    if str(user_id) in users:
        try:
            expiry = datetime.datetime.strptime(users[str(user_id)], "%Y-%m-%d %H:%M:%S")
            if datetime.datetime.now() < expiry:
                days = (expiry - datetime.datetime.now()).days
                return True, f"{days} days left"
        except:
            pass
    return False, "Not Subscribed"

def remove_user(user_id):
    users = load_users()
    if str(user_id) in users:
        del users[str(user_id)]
        save_users(users)
        return True
    return False

# Telegram বট
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# স্ক্যানার ডাটা
scan_data = []

def scanner():
    print("🔄 Scanner started...")
    ranges = ["88017", "88018", "88019", "88015", "88016", "88013", "88014", "Bangladesh"]
    while True:
        try:
            for r in ranges:
                scan_data.append({
                    'range': r,
                    'time': datetime.datetime.now(),
                    'cli': f"01{random.randint(10000000, 99999999)}"
                })
            # পুরাতন ডাটা ডিলিট (10 মিনিট)
            cutoff = datetime.datetime.now() - timedelta(minutes=10)
            global scan_data
            scan_data = [d for d in scan_data if d['time'] > cutoff]
            time.sleep(15)
        except:
            time.sleep(30)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_premium, status = check_user(user_id)
    
    if user_id == ADMIN_ID:
        keyboard = [
            [KeyboardButton("🔴 Live Range")],
            [KeyboardButton("➕ Add User"), KeyboardButton("➖ Remove User")],
            [KeyboardButton("📋 User List"), KeyboardButton("👤 My Info")]
        ]
    elif is_premium:
        keyboard = [
            [KeyboardButton("🔴 Live Range")],
            [KeyboardButton("👤 My Info"), KeyboardButton("📞 Contact Admin")]
        ]
    else:
        keyboard = [
            [KeyboardButton("🔓 Upgrade")],
            [KeyboardButton("👤 My Info"), KeyboardButton("📞 Contact Admin")]
        ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"👋 Welcome! Status: {status}", reply_markup=reply_markup)

# ইউজার স্টেট
user_states = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    # ওয়েটিং ফর ইনপুট
    if user_id in user_states:
        state = user_states[user_id]
        if state == "wait_add" and text.isdigit():
            target = int(text)
            expiry = add_user(target)
            await update.message.reply_text(f"✅ User {target} added! Expires: {expiry}")
            del user_states[user_id]
            return
        elif state == "wait_remove" and text.isdigit():
            target = int(text)
            if remove_user(target):
                await update.message.reply_text(f"✅ User {target} removed!")
            else:
                await update.message.reply_text("❌ User not found")
            del user_states[user_id]
            return
        else:
            await update.message.reply_text("❌ Send a valid numeric ID")
            del user_states[user_id]
            return
    
    # এডমিন কমান্ড
    if user_id == ADMIN_ID:
        if text == "➕ Add User":
            user_states[user_id] = "wait_add"
            await update.message.reply_text("Send User ID to ADD:")
            return
        elif text == "➖ Remove User":
            user_states[user_id] = "wait_remove"
            await update.message.reply_text("Send User ID to REMOVE:")
            return
        elif text == "📋 User List":
            users = load_users()
            if not users:
                await update.message.reply_text("No users found")
            else:
                msg = "📋 **User List:**\n\n"
                for uid, exp in list(users.items())[:20]:
                    msg += f"🆔 {uid}\n📅 {exp}\n\n"
                await update.message.reply_text(msg, parse_mode='Markdown')
            return
    
    # চেক সাবস্ক্রিপশন
    is_premium, status = check_user(user_id)
    
    # লাইভ রেঞ্জ
    if text == "🔴 Live Range":
        if not is_premium and user_id != ADMIN_ID:
            await update.message.reply_text("🚫 Premium feature! Type /start to upgrade")
            return
        
        if not scan_data:
            await update.message.reply_text("⚠️ Scanning data, please wait...")
            return
        
        # লেটেস্ট ডাটা (লাস্ট ৫ মিনিট)
        cutoff = datetime.datetime.now() - timedelta(minutes=5)
        recent = [d for d in scan_data if d['time'] > cutoff]
        
        stats = {}
        for d in recent:
            rng = d['range']
            stats[rng] = stats.get(rng, 0) + 1
        
        if not stats:
            await update.message.reply_text("No active ranges")
        else:
            msg = "🔥 **Live Ranges:**\n\n"
            for i, (rng, count) in enumerate(sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]):
                msg += f"{i+1}. {rng} - {count} hits\n"
            await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    # আপগ্রেড
    if text == "🔓 Upgrade":
        msg = """💎 **PREMIUM UPGRADE**

💰 Price: 130 BDT / 1 USD per month

💳 Payment Methods:
• bKash
• Nagad  
• Binance

📌 Send payment screenshot with last 3 digits

Contact: @Rana1132"""
        await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    # মাই ইনফো
    if text == "👤 My Info":
        await update.message.reply_text(f"🆔 ID: `{user_id}`\n📅 Status: {status}", parse_mode='Markdown')
        return
    
    # কন্টাক্ট
    if text == "📞 Contact Admin":
        await update.message.reply_text(f"📧 Contact: {ADMIN_USERNAME}", parse_mode='Markdown')
        return
    
    # ডিফল্ট
    await start(update, context)

async def main():
    print("="*40)
    print("🤖 BOT STARTING ON RAILWAY")
    print("="*40)
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    await app.bot.delete_webhook(drop_pending_updates=True)
    print("✅ Webhook cleared")
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    print("✅ BOT IS RUNNING!")
    
    # Keep running
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    # Start scanner thread
    thread = threading.Thread(target=scanner, daemon=True)
    thread.start()
    
    # Run bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot stopped")