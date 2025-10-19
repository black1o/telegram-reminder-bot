import os
import json
import time
import threading
import schedule
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

print("🤖 Starting Telegram Reminder Bot...")

# Get bot token from environment
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ ERROR: No BOT_TOKEN found!")
    exit(1)

print("✅ Bot token found")

# Storage
REMINDERS_FILE = 'reminders.json'

class ReminderBot:
    def __init__(self):
        self.reminders = self.load_reminders()
    
    def load_reminders(self):
        try:
            with open(REMINDERS_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_reminders(self):
        with open(REMINDERS_FILE, 'w') as f:
            json.dump(self.reminders, f, indent=2)
    
    def add_reminder(self, user_id, event_name, event_date, event_time):
        reminder_id = f"{user_id}_{int(time.time())}"
        event_datetime = f"{event_date} {event_time}"
        
        self.reminders[reminder_id] = {
            'user_id': user_id,
            'event_name': event_name,
            'event_datetime': event_datetime,
            'reminder_sent': False
        }
        self.save_reminders()
        return reminder_id

# Global bot instance
bot_instance = ReminderBot()

async def start(update: Update, context: CallbackContext):
    keyboard = [['📅 Add Reminder', '📋 My Reminders'], ['ℹ️ Help']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🤖 **Reminder Bot**\n\n"
        "I'll help you remember important events!\n"
        "Use the buttons below:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: CallbackContext):
    help_text = """
ℹ️ **How to use:**

**Set Reminder:**
Click 'Add Reminder' or send:
`/remind Event Name - YYYY-MM-DD - HH:MM`

**Example:**
`/remind Meeting - 2024-12-25 - 14:30`

**View Reminders:**
Click 'My Reminders' or send `/list`

I'll remind you 30 minutes before each event! 🔔
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def remind_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    try:
        text = update.message.text.replace('/remind', '').strip()
        parts = [part.strip() for part in text.split('-') if part.strip()]
        
        if len(parts) != 3:
            await update.message.reply_text(
                "❌ **Format:** `/remind Event Name - YYYY-MM-DD - HH:MM`\n\n"
                "**Example:**\n`/remind Meeting - 2024-12-25 - 14:30`",
                parse_mode='Markdown'
            )
            return
        
        event_name, event_date, event_time = parts
        
        # Validate
        datetime.strptime(event_date, '%Y-%m-%d')
        datetime.strptime(event_time, '%H:%M')
        
        # Add reminder
        reminder_id = bot_instance.add_reminder(user_id, event_name, event_date, event_time)
        
        await update.message.reply_text(
            f"✅ **Reminder Set!**\n\n"
            f"**Event:** {event_name}\n"
            f"**When:** {event_date} {event_time}\n"
            f"**Reminder:** 30 minutes before\n\n"
            f"I'll notify you! 🔔",
            parse_mode='Markdown'
        )
        
    except ValueError:
        await update.message.reply_text(
            "❌ **Invalid format!**\n\n"
            "**Date:** YYYY-MM-DD (2024-12-25)\n"
            "**Time:** HH:MM (14:30)\n\n"
            "**Example:**\n`/remind Meeting - 2024-12-25 - 14:30`",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text("❌ Error setting reminder.")

async def list_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_reminders = []
    
    for reminder_id, reminder in bot_instance.reminders.items():
        if str(reminder['user_id']) == str(user_id) and not reminder['reminder_sent']:
            user_reminders.append(reminder)
    
    if not user_reminders:
        await update.message.reply_text("📭 You have no active reminders.")
        return
    
    message = "📋 **Your Reminders:**\n\n"
    for i, reminder in enumerate(user_reminders, 1):
        message += f"{i}. **{reminder['event_name']}**\n   🕐 {reminder['event_datetime']}\n\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def add_reminder_btn(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "📝 To add a reminder, send:\n\n"
        "`/remind Event Name - YYYY-MM-DD - HH:MM`\n\n"
        "**Example:**\n"
        "`/remind Team Meeting - 2024-12-25 - 14:30`",
        parse_mode='Markdown'
    )

async def my_reminders_btn(update: Update, context: CallbackContext):
    await list_command(update, context)

async def help_btn(update: Update, context: CallbackContext):
    await help_command(update, context)

def check_reminders():
    """Check and send due reminders"""
    current_time = datetime.now()
    
    for reminder_id, reminder in bot_instance.reminders.items():
        if reminder['reminder_sent']:
            continue
            
        try:
            event_dt = datetime.strptime(reminder['event_datetime'], '%Y-%m-%d %H:%M')
            reminder_time = event_dt - timedelta(minutes=30)
            
            if current_time >= reminder_time:
                # Mark as sent (we'll implement actual sending later)
                reminder['reminder_sent'] = True
                print(f"🔔 Due: {reminder['event_name']} for user {reminder['user_id']}")
                
        except Exception as e:
            print(f"Error checking reminder: {e}")
    
    bot_instance.save_reminders()

def reminder_worker():
    """Background worker"""
    print("⏰ Starting reminder worker...")
    schedule.every(1).minutes.do(check_reminders)
    
    while True:
        schedule.run_pending()
        time.sleep(30)

def main():
    print("🔧 Initializing bot...")
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("remind", remind_command))
    app.add_handler(CommandHandler("list", list_command))
    
    # Button handlers
    app.add_handler(MessageHandler(filters.Regex('^(📅 Add Reminder)$'), add_reminder_btn))
    app.add_handler(MessageHandler(filters.Regex('^(📋 My Reminders)$'), my_reminders_btn))
    app.add_handler(MessageHandler(filters.Regex('^(ℹ️ Help)$'), help_btn))
    
    # Start background worker
    worker_thread = threading.Thread(target=reminder_worker, daemon=True)
    worker_thread.start()
    
    print("✅ Bot starting...")
    app.run_polling()

if __name__ == '__main__':
    main()
