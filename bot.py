import subprocess
import sys

# Встановлення залежностей з requirements.txt
def install_dependencies():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        sys.exit(1)

install_dependencies()


import requests
from bs4 import BeautifulSoup
import telebot
import threading
import time

API_TOKEN = '7066163975:AAEaBsjDxYj7IibkgOsyl1YfZTJ7g7CN5hg'

bot = telebot.TeleBot(API_TOKEN)

# Storing tracked profiles
tracked_users = {}

# Command to start tracking a user
@bot.message_handler(commands=['track'])
def track_user(message):
    try:
        if len(message.text.split()) < 2:
            bot.reply_to(message, "Please provide a username in the format /track username. For example: /track nik_name055")
            return

        username = message.text.split()[1].lstrip('@')
        user_profile = parse_telegram_profile(username)

        if user_profile:
            tracked_users[username] = {
                'last_profile': user_profile,
                'chat_id': message.chat.id
            }
            send_profile_data(message.chat.id, user_profile, username)
            bot.reply_to(message, f"Started tracking changes for {username}!")
        else:
            bot.reply_to(message, f"Could not find a profile for {username}. Make sure the username is correct.")
    except Exception as e:
        bot.reply_to(message, "An error occurred while processing your request. Please try again.")
        print(f"Error: {e}")

# Command to list all tracked profiles
@bot.message_handler(commands=['list'])
def list_tracked_users(message):
    if tracked_users:
        response = "Currently tracking the following users:\n"
        response += "\n".join([f"{i+1}. {user}" for i, user in enumerate(tracked_users)])
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "No users are currently being tracked.")

# Command to delete a tracked user
@bot.message_handler(commands=['del'])
def delete_tracked_user(message):
    if not tracked_users:
        bot.reply_to(message, "No users are currently being tracked.")
        return

    response = "Select the number of the user you want to stop tracking:\n"
    response += "\n".join([f"{i+1}. {user}" for i, user in enumerate(tracked_users)])
    bot.reply_to(message, response)

    bot.register_next_step_handler(message, process_deletion)

def process_deletion(message):
    try:
        user_index = int(message.text.strip()) - 1
        if 0 <= user_index < len(tracked_users):
            username = list(tracked_users.keys())[user_index]
            del tracked_users[username]
            bot.reply_to(message, f"Stopped tracking {username}.")
        else:
            bot.reply_to(message, "Invalid selection. Please try again.")
    except ValueError:
        bot.reply_to(message, "Invalid input. Please enter a number corresponding to the user you want to stop tracking.")

# Error handler
def handle_error(e):
    print(f"Error: {e}")
    bot.reply_to(message, "An unexpected error occurred. Please try again later.")

# Parsing Telegram profile page
def parse_telegram_profile(username):
    url = f'https://t.me/{username}'
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        photo = soup.find('img', class_='tgme_page_photo_image')
        photo_url = photo['src'].strip() if photo else None

        name_div = soup.find('div', class_='tgme_page_title')
        name = name_div.find('span').text.strip() if name_div else None

        if not name:
            bot.reply_to(message, f"User with username {username} does not exist.")
            return None

        username_div = soup.find('div', class_='tgme_page_extra')
        parsed_username = username_div.text.strip() if username_div else 'Username not available'

        description_div = soup.find('div', class_='tgme_page_description')
        description = description_div.text.strip() if description_div else 'Description not available'

        return {
            'photo': photo_url,
            'name': name,
            'username': parsed_username,
            'description': description
        }
    except Exception as e:
        handle_error(e)
        return None

# Sending profile data
def send_profile_data(chat_id, profile, username):
    caption = f"Name: {profile['name']}\n"
    caption += f"Username: {profile['username']}\n"
    caption += f"Description: {profile['description']}"

    if profile['photo']:
        bot.send_photo(chat_id, profile['photo'], caption=caption)
    else:
        bot.send_message(chat_id, f"No photo available.\n\n{caption}")

# Function to identify changes in the profile
def get_changes(old_profile, new_profile):
    changes = []
    for key in old_profile:
        if old_profile[key] != new_profile[key]:
            if key == 'photo':
                changes.append({
                    'type': 'photo',
                    'old': old_profile[key],
                    'new': new_profile[key]
                })
            else:
                changes.append(f"{key.capitalize()} changed from '{old_profile[key]}' to '{new_profile[key]}'")
    return changes

# Checking for profile changes
def check_for_changes():
    while True:
        for username, info in tracked_users.items():
            new_profile = parse_telegram_profile(username)
            if new_profile and new_profile != info['last_profile']:
                changes = get_changes(info['last_profile'], new_profile)
                for change in changes:
                    if isinstance(change, dict) and change['type'] == 'photo':
                        caption = f"Profile photo changed for {username}.\nOld photo:"
                        bot.send_photo(info['chat_id'], change['old'], caption=caption)
                        bot.send_photo(info['chat_id'], change['new'], caption="New photo:")
                    else:
                        bot.send_message(info['chat_id'], f"Changes detected for {username}:\n{change}")
                tracked_users[username]['last_profile'] = new_profile
        time.sleep(5)  # Checking every 5 seconds

# Start command with instructions
@bot.message_handler(commands=['start'])
def start(message):
    welcome_message = (
        "Welcome to the Telegram Profile Tracker Bot!\n"
        "Commands you can use:\n"
        "/track <username> - Start tracking changes in a user's profile.\n"
        "/list - See all users you are currently tracking.\n"
        "/del - Stop tracking a user.\n"
        "For any questions, contact @i_anonimus."
    )
    bot.reply_to(message, welcome_message)

# Launch change checker in a separate thread
thread = threading.Thread(target=check_for_changes)
thread.start()

# Start bot polling
bot.polling()
