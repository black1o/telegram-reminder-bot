import os
import json
import schedule
import time
import threading
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Bot configuration
BOT_TOKEN = os.environ.get('7757168173:AAGMHJSW6TuYIS1gMCBvauRdxGm5q6zB-FE')
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
    
    def add_reminder(self, user_id, event_name, event_datetime, reminder_minutes=30):
        reminder_id = f"{user_id}_{int(time.time())}"
        self.reminders[reminder_id] = {
            'user_id': user_id,
            'event_name': event_name,
            'event_datetime': event_datetime,
            'reminder_minutes': reminder_minutes,
            'reminder_sent': False
        }
        self.save_reminders()
        return reminder_id

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['📅 Add Reminder', '📋 My Reminders'], ['ℹ️ Help']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🤖 Welcome to Reminder Bot! I'll help you set event reminders.\nChoose an option:",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 How to use:\n"
        "• Click 'Add Reminder' to set new reminder\n"
        "• 'My Reminders' to view your reminders\n"
        "• I'll notify you automatically!"
    )

def check_reminders(app):
    bot = app.bot_data.get('reminder_bot')
    if not bot: return
    
    current_time = datetime.now()
    for reminder_id, reminder in bot.reminders.items():
        if reminder['reminder_sent']: continue
        
        event_time = datetime.fromisoformat(reminder['event_datetime'])
        reminder_time = event_time - timedelta(minutes=reminder['reminder_minutes'])
        
        if current_time >= reminder_time:
            try:
                app.bot.send_message(
                    chat_id=reminder['user_id'],
                    text=f"🔔 Reminder!\n\nEvent: {reminder['event_name']}\nTime: {event_time.strftime('%Y-%m-%d %H:%M')}"
                )
                reminder['reminder_sent'] = True
            except Exception as e:
                print(f"Failed to send reminder: {e}")
    bot.save_reminders()

def reminder_scheduler(app):
    schedule.every(1).minutes.do(lambda: check_reminders(app))
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    reminder_bot = ReminderBot()
    application.bot_data['reminder_bot'] = reminder_bot
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Regex('^(📅 Add Reminder)$'), start))
    application.add_handler(MessageHandler(filters.Regex('^(📋 My Reminders)$'), help_command))
    application.add_handler(MessageHandler(filters.Regex('^(ℹ️ Help)$'), help_command))
    
    # Start scheduler
    scheduler_thread = threading.Thread(target=reminder_scheduler, args=(application,), daemon=True)
    scheduler_thread.start()
    
    print("🤖 Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
