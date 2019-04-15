# -*- coding: utf-8 -*-
import json
import requests
from telegram import KeyboardButton, ReplyKeyboardMarkup

from emojis import *

# TAREAS
def tasks(id, bot, mycol, message, result):
    # API - Consulta de las tareas disponibles
    actual_group = result['group']['id_group']
    url = 'http://localhost:3000/api/chatbot/v1/groups/' + str(actual_group)
    header = {'Authorization': 'Bearer ' + result['user_token']}
    response = requests.get(url, headers=header)
    tasks_hashtable = {}
    if response.status_code == 200:
        response_json = json.loads(response.text)
        for task in response_json['tasks']:
            try:
                tasks_hashtable[task['id']] = {'name' : task['name'], 'actual_item' : task['answer_count'], 'total_items' : task['item_count'], 'task_user_instance_id' : task['task_user_instance_id']}
            except:
                tasks_hashtable[task['id']] = {'name' : task['name'], 'actual_item' : task['answer_count'], 'total_items' : task['item_count'], 'task_user_instance_id' : None}
    if len(tasks_hashtable) > 0:
        keyboard_array = []
        for task in tasks_hashtable.keys():
            keyboard_array.append([tasks_hashtable[task]['name'] + ' [' + str(tasks_hashtable[task]['actual_item']) + '/' + str(tasks_hashtable[task]['total_items']) + ']'])
        keyboard_array.append([emoji_run_girl + " Salir"])
        mycol.update( { 'id_telegram' : id }, { '$set': { 'tasks_options' :  json.dumps(tasks_hashtable, ensure_ascii=False) } })
        keyboard = ReplyKeyboardMarkup(keyboard_array, one_time_keyboard=True)
        bot.sendMessage(chat_id=id, text= 'Selecciona una de las tareas disponibles', reply_markup=keyboard)
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'TAREA_SELECCIONADA' } })
    else:
        bot.sendMessage(chat_id=id, text= 'No hay tareas disponibles')
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU' } })

# TAREA_SELECCIONADA
def task_selected(id, bot, mycol, message, result):
    tasks_hashtable = json.loads(result["tasks_options"])
    tasks_names = []
    tasks_id = []
    for task in tasks_hashtable.keys():
        tasks_names.append(tasks_hashtable[task]["name"] + " [" + str(tasks_hashtable[task]["actual_item"]) + "/" + str(tasks_hashtable[task]["total_items"]) + "]")
        tasks_id.append(task)
    if message not in tasks_names:
        if message[3:] == 'Salir':
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'VOLVER_MENU' } })
        else:
            bot.sendMessage(chat_id=id, text="Opción no valida")
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state': 'TAREAS' } })
    else:
        id_task = tasks_id[tasks_names.index(str(message))]
        task_name = str(message).split('[')[0][:-1]
        task_user_instance_id = tasks_hashtable[id_task]['task_user_instance_id']
        total_items = tasks_hashtable[id_task]["total_items"]

        bot.sendMessage(chat_id=id, text='Has seleccionado la tarea "' + task_name + '".')
        if task_user_instance_id != None:
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM', 'task' : {'id_task' : id_task, 'name' : task_name, 'task_user_instance_id' : task_user_instance_id, 'total_items' :  total_items} } } )
        else:
            # Se crea el task_user_instance_id si no existe
            url = 'http://localhost:3000/api/chatbot/v1/task_user_instances/'
            header = {'Authorization': 'Bearer ' + result['user_token']}
            data = { "task_id" : id_task}
            response = requests.post(url, data=data, headers=header)

            if response.status_code == 200:
                response_json = json.loads(response.text)
                mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM', 'task' : {'id_task' : id_task, 'name' : task_name, 'task_user_instance_id' : response_json['id'], 'total_items' :  total_items } } } )

# TAREA_TERMINADA
def task_finished(id, bot, mycol, message, result):
    task_user_instance_id = result['task']['task_user_instance_id']

    # Obtener la informacion de la tarea terminada
    url = 'http://localhost:3000/api/chatbot/v1/task_user_instances/' + str(task_user_instance_id) + "/results"
    header = {'Authorization': 'Bearer ' + result['user_token']}
    response = requests.get(url, headers=header)

    task_score = 0
    achievements = []

    if response.status_code == 200:
        response_json = json.loads(response.text)
        task_score = response_json['task_score']
        achievements = response_json['achievements']


    bot.sendMessage(chat_id=id, text= "Tarea: " + result['task']['name'])
    bot.sendMessage(chat_id=id, text= "Puntos Obtenidos: " + str(task_score))


    if len(achievements) == 0:
        bot.sendMessage(chat_id=id, text= "No obtuviste logros en esta tarea. ")
    else:
        bot.sendMessage(chat_id=id, text= "Logros: ")
        for achievement in range(len(achievements)):
            bot.sendPhoto(chat_id=id, photo = str(achievements[achievement]['picture_url']))
            bot.sendMessage(chat_id=id, text= achievements[achievement]['name'])
            bot.sendMessage(chat_id=id, text= achievements[achievement]['description'])

    bot.sendMessage(chat_id=id, text= 'Tarea terminada')
    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU' , 'task' : None } })
