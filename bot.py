import os
import json
import time
import threading
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

print("🤖 Starting Reminder Bot...")

# Get bot token from environment
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ ERROR: No BOT_TOKEN found!")
    exit(1)

REMINDERS_FILE = 'reminders.json'

class ReminderBot:
    def __init__(self):
        self.reminders = self.load_reminders()
        print(f"📊 Loaded {len(self.reminders)} reminders")
    
    def load_reminders(self):
        try:
            with open(REMINDERS_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_reminders(self):
        with open(REMINDERS_FILE, 'w') as f:
            json.dump(self.reminders, f, indent=2)
    
    def add_reminder(self, user_id, event_name, event_date, event_time, reminder_minutes=30):
        reminder_id = f"{user_id}_{int(time.time())}"
        event_datetime = f"{event_date} {event_time}"
        
        self.reminders[reminder_id] = {
            'user_id': user_id,
            'event_name': event_name,
            'event_datetime': event_datetime,
            'reminder_minutes': reminder_minutes,
            'reminder_sent': False
        }
        
        self.save_reminders()
        print(f"✅ Added reminder: {event_name} for user {user_id}")
        return reminder_id

# Create bot instance
reminder_bot = ReminderBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ['📅 Add Reminder', '📋 My Reminders'],
        ['🆘 Help', '❌ Cancel']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🤖 **Reminder Bot**\n\n"
        "I'll help you remember important events!\n"
        "Choose an option below:",
        reply_markup=reply_markup
    )

async def handle_add_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 To add a reminder, send:\n"
        "`/remind Event Name - YYYY-MM-DD - HH:MM`\n\n"
        "Example:\n"
        "`/remind Team Meeting - 2024-12-25 - 14:30`\n\n"
        "I'll remind you 30 minutes before the event!",
        parse_mode='Markdown'
    )

async def handle_my_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_reminders = []
    
    for reminder_id, reminder in reminder_bot.reminders.items():
        if str(reminder['user_id']) == str(user_id) and not reminder['reminder_sent']:
            user_reminders.append(reminder)
    
    if not user_reminders:
        await update.message.reply_text("📭 You have no active reminders.")
        return
    
    message = "📋 **Your Reminders:**\n\n"
    for i, reminder in enumerate(user_reminders, 1):
        message += (
            f"{i}. **{reminder['event_name']}**\n"
            f"   🕐 {reminder['event_datetime']}\n"
            f"   ⏰ {reminder['reminder_minutes']}min before\n\n"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def handle_remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.replace('/remind', '').strip()
        parts = [part.strip() for part in text.split('-') if part.strip()]
        
        if len(parts) != 3:
            await update.message.reply_text(
                "❌ Format: `/remind Event Name - YYYY-MM-DD - HH:MM`\n"
                "Example: `/remind Meeting - 2024-12-25 - 14:30`",
                parse_mode='Markdown'
            )
            return
        
        event_name, event_date, event_time = parts
        
        # Validate date
        datetime.strptime(event_date, '%Y-%m-%d')
        datetime.strptime(event_time, '%H:%M')
        
        # Add reminder
        reminder_id = reminder_bot.add_reminder(
            user_id=update.effective_user.id,
            event_name=event_name,
            event_date=event_date,
            event_time=event_time,
            reminder_minutes=30
        )
        
        await update.message.reply_text(
            f"✅ **Reminder Set!**\n\n"
            f"**Event:** {event_name}\n"
            f"**Date:** {event_date}\n"
            f"**Time:** {event_time}\n"
            f"**Reminder:** 30 minutes before\n\n"
            f"I'll notify you! 🔔",
            parse_mode='Markdown'
        )
        
    except ValueError as e:
        await update.message.reply_text(
            "❌ **Invalid format!**\n\n"
            "Use: `/remind Event Name - YYYY-MM-DD - HH:MM`\n"
            "• Date format: 2024-12-31\n"
            "• Time format: 14:30 (24-hour)",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text("❌ Error setting reminder. Please try again.")

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🆘 **Help Guide**

**Commands:**
/start - Start the bot
/remind - Set a new reminder
/help - Show this help

**Set Reminder:**
`/remind Event Name - YYYY-MM-DD - HH:MM`

**Examples:**
`/remind Birthday Party - 2024-12-25 - 18:00`
`/remind Doctor Appointment - 2024-11-15 - 10:30`

**Features:**
• Automatic reminders 30 minutes before
• View all your reminders
• 24/7 reliable service
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.")

def check_and_send_reminders(app):
    """Check for due reminders and send them"""
    current_time = datetime.now()
    reminders_sent = 0
    
    for reminder_id, reminder in reminder_bot.reminders.items():
        if reminder['reminder_sent']:
            continue
        
        try:
            event_datetime = datetime.strptime(reminder['event_datetime'], '%Y-%m-%d %H:%M')
            reminder_time = event_datetime - timedelta(minutes=reminder['reminder_minutes'])
            
            if current_time >= reminder_time:
                # Send reminder
                app.bot.send_message(
                    chat_id=reminder['user_id'],
                    text=f"🔔 **REMINDER!**\n\n"
                         f"**{reminder['event_name']}**\n"
                         f"Starts at: {reminder['event_datetime']}\n\n"
                         f"Don't forget! 🎯"
                )
                reminder['reminder_sent'] = True
                reminders_sent += 1
                print(f"📨 Sent reminder: {reminder['event_name']}")
                
        except Exception as e:
            print(f"❌ Error processing reminder {reminder_id}: {e}")
    
    if reminders_sent > 0:
        reminder_bot.save_reminders()
        print(f"✅ Sent {reminders_sent} reminders")

def reminder_worker(app):
    """Background worker to check reminders every minute"""
    print("🕐 Starting reminder worker...")
    while True:
        try:
            check_and_send_reminders(app)
            time.sleep(60)  # Check every minute
        except Exception as e:
            print(f"❌ Worker error: {e}")
            time.sleep(30)

def main():
    print("🚀 Initializing Telegram Bot...")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("remind", handle_remind_command))
    application.add_handler(CommandHandler("help", handle_help))
    
    # Message handlers for buttons
    application.add_handler(MessageHandler(filters.Regex('^(📅 Add Reminder)$'), handle_add_reminder))
    application.add_handler(MessageHandler(filters.Regex('^(📋 My Reminders)$'), handle_my_reminders))
    application.add_handler(MessageHandler(filters.Regex('^(🆘 Help)$'), handle_help))
    application.add_handler(MessageHandler(filters.Regex('^(❌ Cancel)$'), handle_cancel))
    
    # Start reminder worker in background
    worker_thread = threading.Thread(target=reminder_worker, args=(application,), daemon=True)
    worker_thread.start()
    
    print("✅ Bot is ready! Starting polling...")
    application.run_polling()

if __name__ == '__main__':
    main()
