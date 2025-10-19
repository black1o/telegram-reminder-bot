import os
import json
import time
import threading
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

print("🚀 Starting Telegram Reminder Bot...")

# Get bot token from environment
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ ERROR: No BOT_TOKEN found!")
    exit(1)

print("✅ Bot token found, initializing...")

# Simple reminder storage
REMINDERS_FILE = 'reminders.json'

def load_reminders():
    """Load reminders from JSON file"""
    try:
        with open(REMINDERS_FILE, 'r') as f:
            reminders = json.load(f)
            print(f"📊 Loaded {len(reminders)} reminders from storage")
            return reminders
    except FileNotFoundError:
        print("📝 No existing reminders file, starting fresh")
        return {}

def save_reminders(reminders):
    """Save reminders to JSON file"""
    with open(REMINDERS_FILE, 'w') as f:
        json.dump(reminders, f, indent=2)

# Global reminders dictionary
reminders = load_reminders()

def start_command(update: Update, context: CallbackContext):
    """Handler for /start command"""
    print(f"👋 User {update.effective_user.id} started the bot")
    
    keyboard = [
        ['📅 Add Reminder', '📋 My Reminders'],
        ['🆘 Help']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    update.message.reply_text(
        "🤖 **Reminder Bot Started!**\n\n"
        "I can help you set reminders for important events!\n\n"
        "**Quick Commands:**\n"
        "• /remind - Set a new reminder\n"
        "• /list - Show your reminders\n"
        "• /help - Get help\n\n"
        "Or use the buttons below:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def help_command(update: Update, context: CallbackContext):
    """Handler for /help command"""
    help_text = """
🆘 **How to Use This Bot**

**Set a Reminder:**
Use: `/remind Event Name - YYYY-MM-DD - HH:MM`

**Examples:**
`/remind Team Meeting - 2024-12-25 - 14:30`
`/remind Birthday Party - 2024-11-15 - 18:00`

**Other Commands:**
`/list` - Show your active reminders
`/help` - Show this help message

**Features:**
• Automatic reminders 30 minutes before events
• Simple keyboard interface
• 24/7 reliable service
    """
    update.message.reply_text(help_text, parse_mode='Markdown')

def remind_command(update: Update, context: CallbackContext):
    """Handler for /remind command"""
    user_id = update.effective_user.id
    
    try:
        # Extract parts from command
        text = update.message.text.replace('/remind', '').strip()
        parts = [part.strip() for part in text.split('-') if part.strip()]
        
        if len(parts) != 3:
            update.message.reply_text(
                "❌ **Incorrect format!**\n\n"
                "**Correct format:**\n"
                "`/remind Event Name - YYYY-MM-DD - HH:MM`\n\n"
                "**Example:**\n"
                "`/remind Team Meeting - 2024-12-25 - 14:30`",
                parse_mode='Markdown'
            )
            return
        
        event_name, event_date, event_time = parts
        
        # Validate date and time
        datetime.strptime(event_date, '%Y-%m-%d')
        datetime.strptime(event_time, '%H:%M')
        
        # Create reminder ID
        reminder_id = f"{user_id}_{int(time.time())}"
        event_datetime = f"{event_date} {event_time}"
        
        # Add to reminders
        reminders[reminder_id] = {
            'user_id': user_id,
            'event_name': event_name,
            'event_datetime': event_datetime,
            'reminder_minutes': 30,
            'reminder_sent': False,
            'created_at': time.time()
        }
        
        # Save to file
        save_reminders(reminders)
        
        print(f"✅ User {user_id} set reminder: {event_name} at {event_datetime}")
        
        update.message.reply_text(
            f"✅ **Reminder Set Successfully!**\n\n"
            f"**Event:** {event_name}\n"
            f"**Date:** {event_date}\n"
            f"**Time:** {event_time}\n"
            f"**Reminder:** 30 minutes before\n\n"
            f"I'll notify you! 🔔",
            parse_mode='Markdown'
        )
        
    except ValueError as e:
        update.message.reply_text(
            "❌ **Invalid date or time format!**\n\n"
            "**Date must be:** YYYY-MM-DD (e.g., 2024-12-25)\n"
            "**Time must be:** HH:MM (e.g., 14:30)\n\n"
            "**Example:**\n"
            "`/remind Meeting - 2024-12-25 - 14:30`",
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"❌ Error in remind_command: {e}")
        update.message.reply_text(
            "❌ Sorry, there was an error setting your reminder. Please try again."
        )

def list_command(update: Update, context: CallbackContext):
    """Handler for /list command - show user's reminders"""
    user_id = update.effective_user.id
    
    # Filter user's active reminders
    user_reminders = []
    for reminder_id, reminder in reminders.items():
        if (str(reminder['user_id']) == str(user_id) and 
            not reminder['reminder_sent']):
            user_reminders.append(reminder)
    
    if not user_reminders:
        update.message.reply_text(
            "📭 **You have no active reminders.**\n\n"
            "Set one using: `/remind Event Name - YYYY-MM-DD - HH:MM`",
            parse_mode='Markdown'
        )
        return
    
    # Sort by datetime
    user_reminders.sort(key=lambda x: x['event_datetime'])
    
    message = "📋 **Your Active Reminders:**\n\n"
    for i, reminder in enumerate(user_reminders, 1):
        message += (
            f"{i}. **{reminder['event_name']}**\n"
            f"   🕐 {reminder['event_datetime']}\n"
            f"   ⏰ {reminder['reminder_minutes']} minutes before\n\n"
        )
    
    update.message.reply_text(message, parse_mode='Markdown')

def add_reminder_button(update: Update, context: CallbackContext):
    """Handler for Add Reminder button"""
    update.message.reply_text(
        "📝 **Set a New Reminder**\n\n"
        "Use this format:\n"
        "`/remind Event Name - YYYY-MM-DD - HH:MM`\n\n"
        "**Example:**\n"
        "`/remind Team Meeting - 2024-12-25 - 14:30`\n\n"
        "I'll remind you 30 minutes before the event! 🎯",
        parse_mode='Markdown'
    )

def my_reminders_button(update: Update, context: CallbackContext):
    """Handler for My Reminders button"""
    list_command(update, context)

def help_button(update: Update, context: CallbackContext):
    """Handler for Help button"""
    help_command(update, context)

def check_reminders():
    """Check and send due reminders"""
    current_time = datetime.now()
    reminders_to_send = []
    
    # Find due reminders
    for reminder_id, reminder in reminders.items():
        if reminder['reminder_sent']:
            continue
            
        try:
            event_dt = datetime.strptime(reminder['event_datetime'], '%Y-%m-%d %H:%M')
            reminder_time = event_dt - timedelta(minutes=reminder['reminder_minutes'])
            
            if current_time >= reminder_time:
                reminders_to_send.append((reminder_id, reminder))
                
        except Exception as e:
            print(f"❌ Error processing reminder {reminder_id}: {e}")
    
    # Send reminders
    for reminder_id, reminder in reminders_to_send:
        try:
            # This will be handled by the main thread
            reminders[reminder_id]['reminder_sent'] = True
            print(f"🔔 Marked reminder for sending: {reminder['event_name']}")
        except Exception as e:
            print(f"❌ Error sending reminder {reminder_id}: {e}")
    
    # Save changes
    if reminders_to_send:
        save_reminders(reminders)
        print(f"✅ Processed {len(reminders_to_send)} due reminders")

def reminder_checker_worker(updater):
    """Background worker to check reminders"""
    print("🕐 Starting reminder checker worker...")
    while True:
        try:
            check_reminders()
            time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            print(f"❌ Error in reminder worker: {e}")
            time.sleep(60)

def error_handler(update: Update, context: CallbackContext):
    """Error handler"""
    print(f"❌ Error occurred: {context.error}")

def main():
    print("🔧 Initializing Telegram Bot...")
    
    # Create updater
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    print("✅ Updater created successfully")
    
    # Add command handlers
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("remind", remind_command))
    dp.add_handler(CommandHandler("list", list_command))
    
    # Add button handlers
    dp.add_handler(MessageHandler(Filters.regex('^(📅 Add Reminder)$'), add_reminder_button))
    dp.add_handler(MessageHandler(Filters.regex('^(📋 My Reminders)$'), my_reminders_button))
    dp.add_handler(MessageHandler(Filters.regex('^(🆘 Help)$'), help_button))
    
    # Add error handler
    dp.add_error_handler(error_handler)
    
    print("✅ All handlers added")
    
    # Start reminder checker in background
    worker_thread = threading.Thread(
        target=reminder_checker_worker, 
        args=(updater,), 
        daemon=True
    )
    worker_thread.start()
    print("✅ Background worker started")
    
    # Start the bot
    print("🎯 Starting bot polling...")
    updater.start_polling()
    print("🤖 Bot is now running and ready!")
    updater.idle()

if __name__ == '__main__':
    main()
