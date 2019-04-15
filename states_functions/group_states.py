# -*- coding: utf-8 -*-
import json
import requests
from telegram import KeyboardButton, ReplyKeyboardMarkup

# GRUPO
def groups(id, bot, mycol, message, result):
    url = 'http://localhost:3000/api/chatbot/v1/groups/'
    header = {'Authorization': 'Bearer ' + result['user_token']}
    response = requests.get(url, headers=header)
    groups_hashtable = {}
    if response.status_code == 200:
        response_json = json.loads(response.text)
        if response_json["groups"] != None:
            for group in response_json["groups"]:
                groups_hashtable[group['id']] = group['name']

    if len(groups_hashtable.keys()) != 0:
        mycol.update( { 'id_telegram' : id }, { '$set': { 'groups_options': json.dumps(groups_hashtable, ensure_ascii=False) } })
        keyboard_array = [[]]
        for group in groups_hashtable.keys():
            keyboard_array.append([groups_hashtable[group]])
        keyboard = ReplyKeyboardMarkup(keyboard_array,  one_time_keyboard=True)
        bot.sendMessage(chat_id=id, text= 'Para comenzar a practicar, selecciona alguno de tus cursos presionando un botón', reply_markup=keyboard)
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state': 'GRUPO_SELECCIONADO' } })
    else:
        bot.sendMessage(chat_id=id, text= 'No hay cursos disponibles')

# GRUPO_SELECCIONADO
def selected_group(id, bot, mycol, message, result):
    groups_hashtable = json.loads(result["groups_options"])
    if message not in groups_hashtable.values():
        bot.sendMessage(chat_id=id, text='No te estoy entendiendo. Intenta usar los botones de abajo.')
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state': 'GRUPO' }} )
    else:
        id_group = 0
        for identifier in groups_hashtable.keys():
            if groups_hashtable[identifier] == message:
                id_group = identifier
        bot.sendMessage(chat_id=id, text='Bienvenido al curso "' + str(message) + '". Puedes comenzar a practicar presionando “Tareas”.')
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU', 'group' : { 'id_group' : int(id_group), 'name' : str(message) }}})

# CAMBIAR_GRUPO
def change_group(id, bot, mycol, message, result):
    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'GRUPO' , 'group' : None} })
