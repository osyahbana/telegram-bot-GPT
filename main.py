import os
import logging
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import openai
import time
from collections import defaultdict


TELEGRAM_API_TOKEN = "INPUT YOUR TOKEN HERE"
OPENAI_API_KEY = "INPUT YOUR API KEY HERE"
WHITELIST = ["*"]
LOG_FOLDER = "log"

openai.api_key = OPENAI_API_KEY
updater = Updater(TELEGRAM_API_TOKEN)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    if user.username in WHITELIST:
        update.message.reply_text(f"Hi {user.username}! You can now chat with the bot. Type /stop to end the conversation.")
    else:
        update.message.reply_text("Sorry, you are not authorized to chat with this bot.")

def stop(update: Update, context: CallbackContext):
    update.message.reply_text("Bye! If you want to start over, type /start.")

chat_histories = defaultdict(list)

def chat(update: Update, context: CallbackContext):
    print(f"Received message from {update.effective_user.username}: {update.message.text}")
    if "*" in WHITELIST or update.effective_user.username in WHITELIST:
        typing = True

        def send_typing():
            while typing:
                context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
                time.sleep(5)

        import threading
        t = threading.Thread(target=send_typing)
        t.start()

        user_message = {"role": "user", "content": update.message.text}
        username = update.effective_user.username
        chat_histories[username].append(user_message)
        openai_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=chat_histories[username],
            max_tokens=2048,
            n=1,
            temperature=0.7,
        )

        typing = False
        message = openai_response['choices'][0]['message']['content'].strip()
        bot_message = {"role": "assistant", "content": message}
        chat_histories[username].append(bot_message)
        update.message.reply_text(message)
        log_conversation(username, update.message.text, message)


def log_conversation(username, user_message, bot_message):
    file_path = os.path.join(LOG_FOLDER, f"{username}_conversation.txt")
    with open(file_path, "a") as log_file:
        log_file.write(f"User: {user_message}\n")
        log_file.write(f"Bot: {bot_message}\n")

if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("stop", stop))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, chat))

updater.start_polling()
updater.idle()
