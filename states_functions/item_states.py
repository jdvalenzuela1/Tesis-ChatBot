# -*- coding: utf-8 -*-
import json
import requests
import datetime
from telegram import KeyboardButton, ReplyKeyboardMarkup

from emojis import *

# ITEM
def items(id, bot, mycol, message, result):
    task_user_instances_id = result['task']['task_user_instance_id']
    token = result['user_token']
    url = 'http://localhost:3000/api/chatbot/v1/task_user_instances/' + str(task_user_instances_id)
    header = {'Authorization': 'Bearer ' + token}
    response = requests.get(url, headers=header)
    items_list = []
    if response.status_code == 200:
        response_json = json.loads(response.text)
        items_list = response_json['items']
        for item in items_list:
            for choice in range(len(item['choices'])):
                item['choices'][choice]['choice_number'] = str(choice + 1) + "."

    if len(items_list) > 0:
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM_DESPLEGAR_INFORMACION', 'to_delete_message_id' : None, 'items_list' :  items_list } })
    else:
        bot.sendMessage(chat_id=id, text= 'Error al conseguir los items')
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU', 'to_delete_message_id' : None }})

# ITEM_DESPLEGAR_INFORMACION
def item_display_information(id, bot, mycol, message, result):
    actual_item = result['items_list'][0]
    item_start_time = datetime.datetime.now()
    # Intenta obtener el tiempo de inicio de la tarea en caso de haberla comenzado anteriormente
    try:
        item_start_time = item_information_hashtable['item_start_time']
    except:
        actual_item['item_start_time'] = item_start_time
    # Intenta mandar la imagen de la pregunta
    url_item = ""
    if actual_item["url_item"] == None:
        url_item = "https://developers.google.com/maps/documentation/streetview/images/error-image-generic.png"
    else:
        url_item = actual_item["url_item"]

    send_photo = bot.sendPhoto(chat_id=id, photo=url_item)
    # Se arman las opciones
    keyboard_array = [[]]
    for choice in actual_item['choices']:
        keyboard_array[0].append(choice['choice_number'])

    keyboard_array.append([emoji_hand + " Ayuda", emoji_run_girl + " Salir"])
    keyboard = ReplyKeyboardMarkup(keyboard_array, resize_keyboard=True, one_time_keyboard=True)
    send_item_count = bot.sendMessage(chat_id=id, text= "Pregunta. " + str(result['task']['total_items'] - len(result['items_list']) + 1) + " de " + str(result['task']['total_items']) +".", reply_markup=keyboard)

    to_delete_message_id = result["to_delete_message_id"]
    if to_delete_message_id == None:
        to_delete_message_id = [send_photo["message_id"], send_item_count["message_id"]]
    else:
        to_delete_message_id.append(send_photo["message_id"])
        to_delete_message_id.append(send_item_count["message_id"])
    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM_SELECCIONADO' , "active_item" : True, "to_delete_message_id" : to_delete_message_id ,'items_list' : result['items_list']}})

# ITEM_SELECCIONADO
def item_selected(id, bot, mycol, message, result):
    if message[3:] == 'Ayuda':
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM_SELECCIONADO_AYUDA' } })
    elif message[3:] == 'Salir':
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'VOLVER_MENU' } })
    else:
        # Validar la opcion puesta por el alumno
        items_list = result['items_list']
        actual_item = items_list[0]
        alternatives = {}
        for choice in range(len(actual_item['choices'])):
            alternatives[actual_item['choices'][choice]['choice_number']] = choice

        # Respuesta del alumno dentro de las opciones ofrecidas
        if message in alternatives.keys():
            # Se registra la informacion de la respuesta ingresada por el alumno
            actual_item['user_choice_id'] = actual_item['choices'][alternatives[message]]['id']
            item_end_time = datetime.datetime.now()
            actual_item["item_end_time"] = item_end_time
            mycol.update( { 'id_telegram' : id }, { '$set': { 'items_list' : items_list} })
            # Respondio correctamente
            if actual_item['choices'][alternatives[message]]['solution']:
                bot.sendMessage(chat_id=id, text= "Respuesta correcta")
                second_attempt = False
                try:
                    second_attempt = actual_item['second_attempt']
                except:
                    pass
                item_start_time = actual_item["item_start_time"]

                # Eliminar todos los comentarios del item mostrados en el chat y agrega el nuevo
                for to_delete_message_id in result['to_delete_message_id']:
                    bot.deleteMessage(chat_id=id, message_id = to_delete_message_id)

                # Se manda la respuesta al servidor
                task_user_instance_id = result['task']['task_user_instance_id']
                item_id = actual_item['id']
                choice_id = actual_item['choices'][alternatives[message]]['id']
                attempt = 1
                if second_attempt:
                    attempt = 2
                response_time_seconds = (item_end_time - item_start_time).total_seconds()

                url = 'http://localhost:3000/api/chatbot/v1/user_responses/'
                header = {'Authorization': 'Bearer ' + result['user_token']}
                data = {'task_user_instance_id' : task_user_instance_id, 'item_id' : item_id, 'choice_id' : choice_id, 'attempt' : attempt, 'response_time_seconds' : response_time_seconds}
                response = requests.post(url, data=data, headers=header)

                # Es el ultimo item de la tarea
                if len(result['items_list']) == 1:
                    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'TAREA_TERMINADA', 'to_delete_message_id' : [] } })
                # Faltan items por responder
                else:
                    items_list.pop(0)
                    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM_DESPLEGAR_INFORMACION', 'items_list' : items_list, 'to_delete_message_id' : [] } })
            # Respondio incorrectamente
            else:
                second_attempt = False
                try:
                    second_attempt = actual_item['second_attempt']
                except:
                    pass

                # Respuesta incorrecta al primer intento
                if not second_attempt:
                    bot.sendMessage(chat_id=id, text= "Respuesta incorrecta. Intenta nuevamente")

                    # Eliminar todos los comentarios del item mostrados en el chat
                    for to_delete_message_id in result['to_delete_message_id']:
                        bot.deleteMessage(chat_id=id, message_id = to_delete_message_id)
                    # Se actualiza la informacion del item
                    actual_item['second_attempt'] = True
                    actual_item['choices'].pop(alternatives[message])

                    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM_DESPLEGAR_INFORMACION',  "to_delete_message_id" : [], "items_list" : items_list } })
                # Respuesta incorrecta al segundo intento
                else:
                    bot.sendMessage(chat_id=id, text= "Respuesta incorrecta. Se te acabaron los intentos")

                    # Eliminar todos los comentarios del item mostrados en el chat
                    for to_delete_message_id in result['to_delete_message_id']:
                        bot.deleteMessage(chat_id=id, message_id = to_delete_message_id)
                    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM_SOLICITUD_AYUDA', 'to_delete_message_id' : [] } } )

        # Respuesta del alumno fuera de las opciones ofrecidas
        else:
            # Eliminar todos los comentarios del item mostrados en el chat
            for to_delete_message_id in result['to_delete_message_id']:
                bot.deleteMessage(chat_id=id, message_id = to_delete_message_id)
            bot.sendMessage(chat_id=id, text= "Debes seleccionar una de las opciones")
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM_DESPLEGAR_INFORMACION', 'to_delete_message_id' : [] } })

# ITEM_SELECCIONADO_AYUDA
def item_selected_help(id, bot, mycol, message, result):
    items_list = result['items_list']
    actual_item = items_list[0]
    feedback = actual_item['feedback']
    # Eliminar todos los comentarios del item mostrados en el chat
    for to_delete_message_id in result['to_delete_message_id']:
        bot.deleteMessage(chat_id=id, message_id = to_delete_message_id)

    if feedback != None:
        bot.sendMessage(chat_id=id, text= str(feedback))
    else:
        bot.sendMessage(chat_id=id, text= "No hay ayudas disponibles")

    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM_DESPLEGAR_INFORMACION' , 'to_delete_message_id' : None} })

# ITEM_SOLICITUD_AYUDA_VALIDACION
def item_request_help_validation(id, bot, mycol, message, result):
    if message[3:] == 'Si':
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM_SOLICITUD_AYUDA_MENSAJE' } })
    elif message[3:] == 'No':
        items_list = result['items_list']
        actual_item = items_list[0]
        # Se manda la respuesta al servidor
        task_user_instance_id = result['task']['task_user_instance_id']
        item_id = actual_item['id']
        choice_id = actual_item['user_choice_id']
        attempt = 2
        item_start_time = actual_item["item_start_time"]
        item_end_time = actual_item["item_end_time"]

        response_time_seconds = (item_end_time - item_start_time).total_seconds()

        url = 'http://localhost:3000/api/chatbot/v1/user_responses/'
        header = {'Authorization': 'Bearer ' + result['user_token']}
        data = {'task_user_instance_id' : task_user_instance_id, 'item_id' : item_id, 'choice_id' : choice_id, 'attempt' : attempt, 'response_time_seconds' : response_time_seconds}
        response = requests.post(url, data=data, headers=header)

        # Es el ultimo item de la tarea
        if len(result['items_list']) == 1:
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'TAREA_TERMINADA', 'to_delete_message_id' : [] } })
        # Faltan items por responder
        else:
            items_list.pop(0)
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM_DESPLEGAR_INFORMACION', 'items_list' : items_list, 'to_delete_message_id' : [] } })
    else:
        bot.sendMessage(chat_id=id, text= "Debes seleccionar una de las opciones")
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM_SOLICITUD_AYUDA' } })

# ITEM_SOLICITUD_AYUDA_MENSAJE
def item_request_help_message(id, bot, mycol, message, result):
    # Intenta mandar la imagen de la pregunta
    actual_item = result['items_list'][0]
    url_item = ""
    if actual_item["url_item"] == None:
        url_item = "https://developers.google.com/maps/documentation/streetview/images/error-image-generic.png"
    else:
        url_item = actual_item["url_item"]
    send_photo = bot.sendPhoto(chat_id=id, photo=url_item)

    bot.sendMessage(chat_id=id, text= "Escribe el mensaje que quieres enviar")
    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM_SOLICITUD_AYUDA_ENVIAR', 'to_delete_message_id' :  [send_photo["message_id"]]} })

# ITEM_SOLICITUD_AYUDA_ENVIAR
def item_request_help_send(id, bot, mycol, message, result):
    items_list = result['items_list']
    actual_item = items_list[0]
    # Se manda la respuesta al servidor
    task_user_instance_id = result['task']['task_user_instance_id']
    item_id = actual_item['id']
    choice_id = actual_item['user_choice_id']
    attempt = 2
    help_message = message
    item_start_time = actual_item["item_start_time"]
    item_end_time = actual_item["item_end_time"]

    response_time_seconds = (item_end_time - item_start_time).total_seconds()

    url = 'http://localhost:3000/api/chatbot/v1/user_responses/'
    header = {'Authorization': 'Bearer ' + result['user_token']}
    data = {'task_user_instance_id' : task_user_instance_id, 'item_id' : item_id, 'choice_id' : choice_id, 'attempt' : attempt, 'help_message': help_message, 'response_time_seconds' : response_time_seconds}
    response = requests.post(url, data=data, headers=header)

    bot.sendMessage(chat_id=id, text= "Mensaje enviado satisfactoriamente")
    # Eliminar todos los comentarios del item mostrados en el chat y agrega el nuevo
    for to_delete_message_id in result['to_delete_message_id']:
        bot.deleteMessage(chat_id=id, message_id = to_delete_message_id)

    # Es el ultimo item de la tarea
    if len(result['items_list']) == 1:
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'TAREA_TERMINADA', 'to_delete_message_id' : [] } })
    # Faltan items por responder
    else:
        items_list.pop(0)
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM_DESPLEGAR_INFORMACION', 'items_list' : items_list, 'to_delete_message_id' : [] } })

# ITEM_SOLICITUD_AYUDA
def item_request_help(id, bot, mycol, message, result):
    keyboard_array = [[emoji_correct + ' Si', emoji_incorrect + ' No']]
    keyboard = ReplyKeyboardMarkup(keyboard_array,  resize_keyboard=True, one_time_keyboard=True)
    bot.sendMessage(chat_id=id, text= "¿Quieres mandar una pregunta sobre este item a un profesor?", reply_markup=keyboard)
    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM_SOLICITUD_AYUDA_VALIDACION' } })
