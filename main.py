from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler
from telegram.ext.filters import *
from keyauth import api
import json as jsond  # json
import time  # sleep before exit
import hmac # signature checksum
import hashlib # signature checksum
import requests
import datetime
import random
import string
from game import modern_strike
from environs import Env
import threading

env = Env()
env.read_env()

TOKEN = env.str("BOT_TOKEN")
ADMIN_LIST = [967948439]

USER, PASS, LICENSE = range(3)
REPORT, TITLE, MESSAGE_TEXT = range(3)

active_timers = {}

keyauthapp = api(
    name = "",
    ownerid = "",
    secret = "",
    version = "",
)

def __do_request(post_data):
        try:
            response = requests.post(
                "https://keyauth.win/api/1.2/", data=post_data, timeout=10
            )
            
            key = keyauthapp.secret if post_data["type"] == "init" else keyauthapp.enckey
                        
            client_computed = hmac.new(key.encode('utf-8'), response.text.encode('utf-8'), hashlib.sha256).hexdigest()
            
            signature = response.headers["signature"]
            
            if not hmac.compare_digest(client_computed, signature):
                print("Signature checksum failed. Request was tampered with or session ended most likely.")
                print("Response: " + response.text)
                time.sleep(3)
            
            return response.text
        except requests.exceptions.Timeout:
            print("Request timed out. Server is probably down/slow at the moment")

def __load_user_data(data):
        keyauthapp.user_data.username = data["username"]
        keyauthapp.user_data.ip = data["ip"]
        keyauthapp.user_data.hwid = data["hwid"] or "N/A"
        keyauthapp.user_data.expires = data["subscriptions"][0]["expiry"]
        keyauthapp.user_data.createdate = data["createdate"]
        keyauthapp.user_data.lastlogin = data["lastlogin"]
        keyauthapp.user_data.subscription = data["subscriptions"][0]["subscription"]
        keyauthapp.user_data.subscriptions = data["subscriptions"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
     user = update.effective_user
     await update.message.reply_markdown_v2(
fr'''
Hello {user.mention_markdown_v2()}, from this bot you can avcite your license \(regist\) or you see your account details such as expires date etc\.\.

How to redeem license?
https://vimeo\.com/manage/videos/843635728

How to start using bot?
It's simple, just choose one of the commands below or by clicking on 𝗠𝗘𝗡𝗨 button and you will be there\.

/status \- check your account infomation
/redeem \- redeem your license key
/dev \- information about the developer
/report \- report for any bugs or problems
''', )
     
async def DeveloperInfo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
     await update.message.reply_text('''
-username: @t_r_y_1 (dm for business only)
-email: BlurryMods@protonmail.com
-github: https://github.com/BlurryMods

C++/'C and Python developer. software/reverse engineer (android game modder) + Telegram/Discrod bot developer.

-modder at: https://polarmods.com/
''')

#login
async def showinfo_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_time = datetime.datetime.now()
    delta = datetime.timedelta(minutes=5)
    new_time = current_time + delta
    new_time_str = new_time.strftime("%H:%M:%S")
    user_id = update.effective_user.id
    if user_id in active_timers:
        await update.message.reply_text(f"Timeout until: {new_time_str} (GMT)")
        return ConversationHandler.END
    await update.message.reply_text("What's your username?")
    return USER


async def showinfo_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
     context.user_data['username'] = update.message.text
     await update.message.reply_text("Great! What's your password?")
     return PASS

async def showinfo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    context.user_data['password'] = update.message.text

    keyauthapp.checkinit()
     
    post_data = {
            "type": "login",
            "username": context.user_data['username'],
            "pass": context.user_data['password'],
            "sessionid": keyauthapp.sessionid,
            "name": keyauthapp.name,
            "ownerid": keyauthapp.ownerid
        }
     
    response = __do_request(post_data)
     
    json = jsond.loads(response)

    if json["success"]:
        __load_user_data(json["info"])
        await update.message.reply_text(f"Successfully logged in!")
        await update.message.reply_text("username: " + context.user_data['username'] + "\n" + "password: " + context.user_data['password'] + "\n" + "IP address: " + keyauthapp.user_data.ip + "\n" + "expires date: " + datetime.datetime.utcfromtimestamp(int(keyauthapp.user_data.expires)).strftime('%Y-%m-%d %H:%M:%S'))
        print("Successfully logged in")
    else:
        print(json["message"])
        await update.message.reply_text(json["message"])
        time.sleep(3)
    
    return ConversationHandler.END

#register
async def redeem_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_time = datetime.datetime.now()
    delta = datetime.timedelta(minutes=5)
    new_time = current_time + delta
    new_time_str = new_time.strftime("%H:%M:%S")
    user_id = update.effective_user.id
    if user_id in active_timers:
        await update.message.reply_text(f"Timeout until: {new_time_str} (GMT)")
        return ConversationHandler.END
     
    await update.message.reply_text("Enter your username:")
    return USER

async def redeem_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
     context.user_data['username'] = update.message.text
     if len(context.user_data['username']) < 4 or len(context.user_data['username']) > 16:
         await update.message.reply_text(f"username should be more then 4 characters and less then 8 characters❌\n\nYour text characters count: {len(context.user_data['username'])}")
         return ConversationHandler.END
     await update.message.reply_text("Great! now send to me a valid license.")
     return LICENSE

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["license"] = update.message.text
    chat_id = update.effective_chat.id
    user_name = update.effective_user.username
    user_id = update.effective_user.id
    full_name = update.effective_user.full_name
    bot_check = update.effective_user.is_bot
    premium_check = update.effective_user.is_premium

    id_random = ''.join(random.choice(string.digits) for i in range(5))
    pass_random = ''.join(random.choice(string.ascii_letters) for i in range(12))
    username = context.user_data['username'] + "#" + id_random

    if len(context.user_data["license"]) != 27:
        await update.message.reply_text("We do not provide licenses of this type.❌")
        # Create a new timer for the user
        timer = threading.Timer(300, timeout, args=[update, context])
        active_timers[user_id] = timer
        timer.start()

        return ConversationHandler.END

    keyauthapp.checkinit()

    post_data = {
            "type": "register",
            "username": username,
            "pass": pass_random,
            "key": context.user_data["license"],
            "sessionid": keyauthapp.sessionid,
            "name": keyauthapp.name,
            "ownerid": keyauthapp.ownerid
        }
     
    response = __do_request(post_data)
     
    json = jsond.loads(response)

    invalid_logger_message = f'''
@{user_name} Failed to register his account!❌

telegram details:
👤full name: {full_name}
🆔user id: {user_id}
🤖is bot?: {bot_check}
📦has premium?: {premium_check}

log message:
{json["message"]}
'''

    logger_message = f'''
@{user_name} has been redeemd a license!✅

telegram details:
👤full name: {full_name}
🆔user id: {user_id}
🤖is bot?: {bot_check}
📦has premium?: {premium_check}

keyauth details:
👤username: {username}
🔑password: {pass_random}
📱IP address: :)
'''

    vaildmessage = f'''
Congratulations [{user_name}]! license has been redeemd and your register has be completed!✅

Username: {username}
Password: {pass_random}
'''

    if json["success"]:
        __load_user_data(json["info"])
        initializing = await update.message.reply_text("initializing your details...⚙️")
        initializing
        time.sleep(5)
        initializing_id = initializing.message_id
        await app.updater.bot.delete_message(chat_id, initializing_id)
        vailddata = await update.message.reply_text("valid details!✅")
        time.sleep(1)
        vailddata
        time.sleep(1)
        vailddata_id = vailddata.message_id
        await app.updater.bot.delete_message(chat_id, vailddata_id)
        setting = await update.message.reply_text("setting your data...⚙️")
        time.sleep(1)
        setting
        time.sleep(5)
        setting_id = setting.message_id
        await app.updater.bot.delete_message(chat_id, setting_id)
        await update.message.reply_text(f"{vaildmessage}" + "\n" + "expires date: " + datetime.datetime.utcfromtimestamp(int(keyauthapp.user_data.expires)).strftime('%Y-%m-%d %H:%M:%S'))
        if context.user_data['license'] in modern_strike:
            await update.message.reply_text("Apk: link\nObb: download the original one from play store")
            modern_strike.remove(f"{context.user_data['license']}")
            await app.updater.bot.sendMessage(chat_id=-1001801720426, message_thread_id=37, text=f"Uesed key:\n{context.user_data['license']}")
            await app.updater.bot.sendMessage(chat_id=-1001801720426, message_thread_id=37, text=f"new list modern strike:\n{modern_strike}")
        else:
            await update.message.reply_text("game not found please contact with admin: @t_r_y_1")
            await app.updater.bot.sendMessage(chat_id=-1001801720426, message_thread_id=2, text=f"{user_name} [ {username} ] is not able to get game apk.❌")

        print("user created Successfully")

        #logs
        await app.updater.bot.sendMessage(chat_id=-1001801720426, message_thread_id=2, text=logger_message)
    else:
        print(json["message"])
        initializing = await update.message.reply_text("initializing your details...⚙️")
        initializing
        time.sleep(5)
        initializing_id = initializing.message_id
        await app.updater.bot.delete_message(chat_id, initializing_id)
        await update.message.reply_text(json["message"])

        #log
        await app.updater.bot.sendMessage(chat_id=-1001801720426, message_thread_id=2, text=invalid_logger_message)
        time.sleep(2)
        await update.message.reply_text("To purchase a vaild key please visit our store:\nhttps://blurrymods.mysellix.io/")
    
    return ConversationHandler.END

def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    del active_timers[user_id]

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Login cancelled.")
    return ConversationHandler.END

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_time = datetime.datetime.now()
    delta = datetime.timedelta(minutes=5)
    new_time = current_time + delta
    new_time_str = new_time.strftime("%H:%M:%S")
    user_id = update.effective_user.id
    if user_id in active_timers:
        await update.message.reply_text(f"Timeout until: {new_time_str} (GMT)")
        return ConversationHandler.END
    id_random = ''.join(random.choice(string.digits) for i in range(6))
    context.user_data['ReportId'] = id_random
    await update.message.reply_text(f"report has been created! Report 🆔: {id_random}")
    await update.message.reply_text("Please enter your report title:")
    return TITLE


async def report_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['ReportTitle'] = update.message.text
    
    if len(context.user_data['ReportTitle']) < 4 or len(context.user_data['ReportTitle']) > 16:
         await update.message.reply_text(f"Report has been canceld⚠️\n\nReason: Report title cannot be less then 4 characters or more then 16 characters❌\n\nYour message characters count: {len(context.user_data['ReportTitle'])}\n\nUse /report command and try again.")
         return ConversationHandler.END
         
    await update.message.reply_text("Great! Please enter your report message:")
    return MESSAGE_TEXT

async def report_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['ReportMessage'] = update.message.text
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    user_id = update.effective_user.id

    if len(context.user_data['ReportMessage']) < 16 or len(context.user_data['ReportMessage']) > 240:
         await update.message.reply_text(f"Report has been canceld⚠️\n\nReason: Report message cannot be less then 16 characters or more then 240 characters❌\n\nYour message characters count: {len(context.user_data['ReportMessage'])}\n\nUse /report command and try again.")
         return ConversationHandler.END

    initializing = await update.message.reply_text("initializing BlurryAuth protection.....")
    initializing
    time.sleep(5)
    initializing_id = initializing.message_id
    await app.updater.bot.delete_message(chat_id, initializing_id)
    safe = await update.message.reply_text("Safe request!✅")
    safe
    time.sleep(3)
    safe_id = safe.message_id
    await app.updater.bot.delete_message(chat_id, safe_id)

    meesage_test = f'''
new report has been taken!🧑‍💻

👤username: @{username}
🆔user id: {user_id}
🎟️report id: {context.user_data['ReportId']}

💾report title:

{context.user_data['ReportTitle']}

📦report message:

{context.user_data['ReportMessage']}
'''

    await app.updater.bot.sendMessage(chat_id=-1001801720426, message_thread_id=64, text=meesage_test)

    await update.message.reply_text("Your report has been sent and you will get response soon.✅")
    return ConversationHandler.END


async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_LIST:
        await update.message.reply_text("you dont have perms to use this command❌")
        return ConversationHandler.END
    await update.message.reply_text("user id:")
    return USER

async def reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['ReplyUserId'] = update.message.text
    await update.message.reply_text("message:")
    return MESSAGE_TEXT

async def reply_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['ReplyMessage'] = update.message.text
    await context.bot.sendMessage(chat_id=context.user_data['ReplyUserId'],text=context.user_data['ReplyMessage'])
    return ConversationHandler.END

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('dev', DeveloperInfo))


status_handler = ConversationHandler(
        entry_points=[CommandHandler('status', showinfo_start)],
        states={
            USER: [MessageHandler(BaseFilter.__text_signature__, showinfo_username)],
            PASS: [MessageHandler(BaseFilter.__text_signature__, showinfo)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )


redeem_handler = ConversationHandler(
        entry_points=[CommandHandler('redeem', redeem_start)],
        states={
            USER: [MessageHandler(BaseFilter.__text_signature__, redeem_username)],
            LICENSE: [MessageHandler(BaseFilter.__text_signature__, redeem)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

report_handler = ConversationHandler(
        entry_points=[CommandHandler('report', report)],
        states={
            TITLE: [MessageHandler(BaseFilter.__text_signature__, report_title)],
            MESSAGE_TEXT: [MessageHandler(BaseFilter.__text_signature__, report_request)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

reply_handler = ConversationHandler(
        entry_points=[CommandHandler('reply', reply)],
        states={
            USER: [MessageHandler(BaseFilter.__text_signature__, reply_message)],
            MESSAGE_TEXT: [MessageHandler(BaseFilter.__text_signature__, reply_request)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

app.add_handler(status_handler)
app.add_handler(redeem_handler)
app.add_handler(report_handler)
app.add_handler(reply_handler)

app.run_polling()