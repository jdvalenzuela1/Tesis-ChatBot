# -*- coding: utf-8 -*-
import json
import requests
from telegram import KeyboardButton, ReplyKeyboardMarkup

from emojis import *

# CONTEXTO
def context(id, bot, mycol, message, result):
    # Verificar si la tarea que se estaba realizando sigue activa
    pending_task = False
    if result['task'] != None:
        task_id = result['task']['id_task']
        actual_group = result['group']['id_group']
        url = 'http://localhost:3000/api/chatbot/v1/groups/' + str(actual_group)
        header = {'Authorization': 'Bearer ' + result['user_token']}
        response = requests.get(url, headers=header)
        tasks_hashtable = {}
        if response.status_code == 200:
            response_json = json.loads(response.text)
            for task in response_json['tasks']:
                if str(task['id']) == str(task_id):
                    pending_task = True
    if pending_task:
        bot.sendMessage(id, 'El curso que estás viendo es "' + str(result['group']['name']) + '" y la tarea que estás resolviendo es "' + str(result['task']['name']) + '".')
        keyboard_array = [[emoji_correct + ' Si', emoji_incorrect + ' No']]
        keyboard = ReplyKeyboardMarkup(keyboard_array,  resize_keyboard=True, one_time_keyboard=True)
        bot.sendMessage(chat_id=id, text= '¿Quieres continuar?', reply_markup=keyboard)
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'CONTEXTO_VALIDAR' } })
    else:
        bot.sendMessage(chat_id=id, text='¿Porque no practicamos un poco te parece?')
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state': 'MENU' }} )

# CONTEXTO_VALIDAR
def context_validate(id, bot, mycol, message, result):
    if message[3:] == 'Si':
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM' } })
    else:
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU' } })
