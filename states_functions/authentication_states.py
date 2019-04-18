# -*- coding: utf-8 -*-
import json
import requests
from telegram import KeyboardButton, ReplyKeyboardMarkup

# Flujo de autentificacion
def authentication_flow(id, bot, mycol, message, result):
    if result['state'] == 'AUTENTIFICACION_VALIDAR_MENU':
        authentication_validate_menu(id=id, bot=bot, mycol=mycol, message=message, result=result)
        result = mycol.find_one( { 'id_telegram': id } )
    if result['state'] == 'AUTENTIFICACION_MENU':
        authentication_menu(id=id, bot=bot, mycol=mycol, message=message, result=result)
    elif result['state'] == 'AUTENTIFICACION_EMAIL':
        authentication_email(id=id, bot=bot, mycol=mycol, message=message, result=result)
    elif result['state'] == 'AUTENTIFICACION_ENVIAR_EMAIL':
        authentication_send_email(id=id, bot=bot, mycol=mycol, message=message, result=result)
    elif result['state'] == 'AUTENTIFICACION_TOKEN':
        authentication_token(id=id, bot=bot, mycol=mycol, message=message, result=result)
    elif result['state'] == 'AUTENTIFICACION_VALIDAR_TOKEN':
        authentication_validate_token(id=id, bot=bot, mycol=mycol, message=message, result=result)

# AUTENTIFICACION_VALIDAR_MENU
def authentication_validate_menu(id, bot, mycol, message, result):
    if message == 'E-mail':
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'AUTENTIFICACION_EMAIL' } })
    elif message == 'Codigo':
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'AUTENTIFICACION_TOKEN' } })
    else:
        bot.sendMessage(chat_id=id, text= "No te estoy entendiendo. Intenta usar los botones de abajo.")
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'AUTENTIFICACION_MENU' } })

# AUTENTIFICACION_MENU
def authentication_menu(id, bot, mycol, message, result):
    keyboard_array = [['Codigo', 'E-mail']]
    keyboard = ReplyKeyboardMarkup(keyboard_array,  resize_keyboard=True, one_time_keyboard=True)
    bot.sendMessage(chat_id=id, text= 'Mira abajo, hay dos botones. Si tienes un código de acceso presiona "Código". En caso contrario, presiona "E-mail".', reply_markup=keyboard)
    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'AUTENTIFICACION_VALIDAR_MENU' } })

# AUTENTIFICACION_EMAIL
def authentication_email(id, bot, mycol, message, result):
    bot.sendMessage(id, 'Ingresa tu correo.')
    mycol.update( { 'id_telegram' : id }, { '$set': { 'state': 'AUTENTIFICACION_ENVIAR_EMAIL' } })

# AUTENTIFICACION_ENVIAR_EMAIL
def authentication_send_email(id, bot, mycol, message, result):
    url = 'http://localhost:3000/api/chatbot/v1/login_email/'
    data = { "email" : message.lower()}
    response = requests.post(url, data=data)

    if response.status_code == 200:
        bot.sendMessage(id, 'Muy bien. Te acabo de enviar un correo que contiene el código para ingresar.')
        mycol.update( { 'id_telegram' : id }, { '$set': { 'user_email': str(message.lower()) } })
    elif response.status_code == 403:
        bot.sendMessage(id, 'El token se creo recientemente. Intentalo luego de 24 horas.')
    else:
        bot.sendMessage(id, 'No existe el correo ingresado en el sistema.')

    keyboard_array = [['Codigo', 'E-mail']]
    keyboard = ReplyKeyboardMarkup(keyboard_array,  resize_keyboard=True, one_time_keyboard=True)
    bot.sendMessage(chat_id=id, text= 'Mira abajo, hay dos botones. Si tienes un código de acceso presiona "Código". En caso contrario, presiona "E-mail".', reply_markup=keyboard)
    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'AUTENTIFICACION_VALIDAR_MENU' } })

# AUTENTIFICACION_TOKEN
def authentication_token(id, bot, mycol, message, result):
    bot.sendMessage(id, 'Ingresa el código para ingresar.')
    mycol.update( { 'id_telegram' : id }, { '$set': { 'state': 'AUTENTIFICACION_VALIDAR_TOKEN' } })

# AUTENTIFICACION_VALIDAR_TOKEN
def authentication_validate_token(id, bot, mycol, message, result):
    url = 'http://localhost:3000/api/chatbot/v1/login_token/'
    data = { "email" : str(result['user_email']), 'token' : str(message)}
    response = requests.post(url, data=data)

    if response.status_code == 200:
        data = json.loads(response.text)

        mycol.update( { 'id_telegram' : id }, { '$set': { 'user_token' : data['token'], 'user_name' : data['name'], 'user_lastname' : data['lastname'], 'state': 'INGRESO' } })
        result = mycol.find_one( { 'id_telegram': id } )
    else:
        bot.sendMessage(id, 'Código incorrecto')
        keyboard_array = [['E-mail', 'Código']]
        keyboard = ReplyKeyboardMarkup(keyboard_array,  resize_keyboard=True, one_time_keyboard=True)
        bot.sendMessage(chat_id=id, text= "Ingresa tu correo para obtener tu token. Selecciona token en caso que ya lo tengas.", reply_markup=keyboard)
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'AUTENTIFICACION_VALIDAR_MENU' } })
