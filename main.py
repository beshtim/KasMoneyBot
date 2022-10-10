import os
from flask import Flask, request
import telebot
from telebot import types
import pandas as pd
import datetime
# -----------SHEETS-----------

from googleapiclient.discovery import build
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = '<GOOGLE CREDENTIALS>' #TODO
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
credentials = None
credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
SAMPLE_SPREADSHEET_ID = '<SHEET ID>' #TODO
service = build('sheets', 'v4', credentials=credentials)

# -------------BOT-------------

token = '<TELEGRAM TOKEN>' #TODO
bot = telebot.TeleBot(token)

global for_add
for_add = {}
# ------------FLASK--------------

server = Flask(__name__)

# -------------------------------


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("➕ Добавить")
    markup.add(btn1)
    bot.send_message(message.chat.id, text="Привет, {0.first_name}! Я помогу тебе заполнить таблицу, НИЧЕГО не пиши мне лишнего, а то я сломаюсь и все ***** рулю.".format(message.from_user))
    bot.send_message(message.chat.id, text="/check - проверить таблицу тут. \n/url - ссыль на таблу\n/sum - прочекать сумму")
    bot.send_message(message.chat.id, text="-------")
    bot.send_message(message.chat.id, text="Если хочешь добавить запись жми кнопку добавить", reply_markup=markup)
    

@bot.message_handler(commands=['sum'])
def sum(message):
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                        range="list!A1:C70").execute()
    values = result.get('values', [])
    print(values)
    df = pd.DataFrame(values)[1:]
    df[1] = df[1].astype(int)
    res = df.groupby(0)[1].agg('sum').reset_index().values
    print(res)
    bot.send_message(message.chat.id, text='Сумма: 👇')
    bot.send_message(message.chat.id, text='\n'.join([' | '.join([str(cell) for cell in row]) for row in res]))
    if len(res) == 2:
        if res[0][0] == 'ПТ':
            pt = res[0][1]
            sv = res[1][1]
        else:
            pt = res[1][1]
            sv = res[0][1]

        if pt > sv: 
            bot.send_message(message.chat.id, text='{}₺ : СВ -> ПТ'.format((pt-sv)//2))
        else:
            bot.send_message(message.chat.id, text='{}₺ : ПТ -> СВ'.format((sv-pt)//2))


@bot.message_handler(commands=['check'])
def check(message):
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                        range="list!A1:D60").execute()
    values = result.get('values', [])
    bot.send_message(message.chat.id, text='\n'.join([' | '.join([str(cell) for cell in row]) for row in values]))

@bot.message_handler(commands=['url'])
def url(message):
    bot.send_message(message.chat.id, text='<table url>')


@bot.message_handler(content_types=['text'])
def func(message):
    if(message.text == "➕ Добавить"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Поля Тима")
        btn2 = types.KeyboardButton("Саша Ваня")
        
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, text="кто добавляет?", reply_markup=markup)
        name = message.from_user.first_name
        for_add[name] = []
    
    elif(message.text == "Поля Тима"):
        bot.send_message(message.chat.id, "Напиши сколько?")
        for_add[message.from_user.first_name].append('ПТ')
    elif message.text == "Саша Ваня":
        bot.send_message(message.chat.id, text="Напиши сколько?")
        for_add[message.from_user.first_name].append('СВ')

    elif message.text not in ["Саша Ваня", "Поля Тима", "➕ Добавить"]:
        if len(for_add[message.from_user.first_name]) == 0:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("Поля Тима")
            btn2 = types.KeyboardButton("Саша Ваня")
            markup.add(btn1, btn2)
            bot.send_message(message.chat.id, text="Надо нажать на кнопку того КТО ДОБАВЛЯЕТ!", reply_markup=markup)
        else:
            try:
                money = int(message.text)
                for_add[message.from_user.first_name].append(money)
                bot.send_message(message.chat.id, text="Комментарий ...")
            except Exception:
                if len(for_add[message.from_user.first_name]) == 1:
                    bot.send_message(message.chat.id, text="Упс это не число, еще раз")
                else:
                    mes = message.text
                    for_add[message.from_user.first_name].append(mes)
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    btn1 = types.KeyboardButton("➕ Добавить")
                    markup.add(btn1)
                    bot.send_message(message.chat.id, text="Готово xD", reply_markup=markup)

    for n in for_add:
        if len(for_add[n]) == 3:
            sheet = service.spreadsheets()
            result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range="list!A1:D60").execute()
            values = result.get('values', [])
            for_add[message.from_user.first_name].append(str(datetime.date.today()))
            values.append(for_add[message.from_user.first_name])
            print(values)
            request = sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                            range='list!A1',
                                            valueInputOption="USER_ENTERED",
                                            body={'values':values}).execute()
            print(request)
            del for_add[n]

@server.route('/' + token, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='<heroku project>' + token) #TODO
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))