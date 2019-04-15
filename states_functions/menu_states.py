# -*- coding: utf-8 -*-
import json
import requests
import datetime
from telegram import KeyboardButton, ReplyKeyboardMarkup

from emojis import *

# Opciones de menu:
# - (1): [Continuar tarea pendiente]: Continuar la ultima tarea visitada en caso de haber.
# - (2): [Tareas]: Se muestran las tareas disponibles en caso de haber.
# - (3): [Logros][Perfil]: Se muestran los logros obtenidos en el curso actual. Se despliega la informacion relacionada al alumno.
# - (4): [Solicitar ayuda][Respuestas recibidas]: Se solicita ayuda sobre el curso en general. Se ven las respuestas recibidas de las solicitudes de ayuda del menu y de los items.
# - (5): [Ranking]: Se ve el ranking de los mejores 10 alumnos en el curso y la posicion actual del alumno.
# - (6): [Cambiar ramo][Cerrar Sesion]

# MENU
def menu(id, bot, mycol, message, result):
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

    mycol.update( { 'id_telegram' : id }, { '$set': { "pending_task" : pending_task,  "to_delete_message_id" : None, "active_item" : False }})

    keyboard_array = [[]]
    if pending_task == True:
        keyboard_array = [[emoji_back + ' Continuar tarea pendiente'],[emoji_task + ' Tareas'], [emoji_hand + ' Solicitar ayuda'], [emoji_books + ' Cambiar ramo', emoji_run_girl + ' Cerrar Sesion']]
        # keyboard_array = [[emoji_back + ' Continuar tarea pendiente'],[emoji_task + ' Tareas'], [emoji_medal + ' Logros', emoji_nerd + ' Perfil'], [emoji_hand + ' Solicitar ayuda'], [emoji_books + ' Cambiar ramo', emoji_run_girl + ' Cerrar Sesion']]
    else:
        keyboard_array = [[emoji_task + ' Tareas'], [emoji_hand + ' Solicitar ayuda'], [emoji_books + ' Cambiar ramo', emoji_run_girl + ' Cerrar Sesion']]
        # keyboard_array = [[emoji_task + ' Tareas'], [emoji_medal + ' Logros', emoji_nerd + ' Perfil'], [emoji_hand + ' Solicitar ayuda'], [emoji_books + ' Cambiar ramo', emoji_run_girl + ' Cerrar Sesion']]

    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU_SELECCIONADO' } })

    keyboard = ReplyKeyboardMarkup(keyboard_array,  one_time_keyboard=True)
    bot.sendMessage(chat_id=id, text= 'Selecciona una de las siguientes opciones', reply_markup=keyboard)

# MENU_SELECCIONADO
def menu_selected(id, bot, mycol, message, result):
    selected_menu_option = True
    if message[3:] == 'Continuar tarea pendiente':
        if result['pending_task'] == True:
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM' } })
        else:
            selected_menu_option = False
    elif message[3:] == 'Tareas':
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'TAREAS' } })
    elif message[3:] == 'Logros':
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'LOGROS' } })
    elif message[3:] == 'Perfil':
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'PERFIL' } })
    elif message[3:] == 'Solicitar ayuda':
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU_SOLICITUD_AYUDA' } })
    elif message[3:] == 'Respuestas recibidas':
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU_RESPUESTAS_RECIBIDAS' } })
    elif message[3:] == 'Cambiar ramo':
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'CAMBIAR_GRUPO' } })
    elif message[3:] == 'Cerrar Sesion':
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'CERRAR_SESION' } })
    else:
        selected_menu_option = False

    if not selected_menu_option:
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'DIALOGO'}})

# VOLVER_MENU
def back_menu(id, bot, mycol, message, result):
    keyboard_array = [[emoji_correct + ' Si', emoji_incorrect + ' No']]
    back_to_menu_text = ""
    # No estamos desarrollando un item
    if not result['active_item']:
        back_to_menu_text = '¿Quieres volver al menu de navegación?'
    # Estamos al medio de un item
    else:
        # Eliminar todos los comentarios del item mostrados en el chat
        if result['to_delete_message_id'] != None:
            for to_delete_message_id in result['to_delete_message_id']:
                bot.deleteMessage(chat_id=id, message_id = to_delete_message_id)
        items_list = result['items_list']
        second_attempt = False
        try:
            second_attempt = items_list[0]['second_attempt']
        except:
            pass
        back_to_menu_text = ""

        if second_attempt:
            back_to_menu_text = '¿Quieres volver al menu de navegación?, tu respuesta se considerara incorrecta'
        else:
            back_to_menu_text = '¿Quieres volver al menu de navegación?, tu respuesta se considerara omitida'

    keyboard = ReplyKeyboardMarkup(keyboard_array,  resize_keyboard=True, one_time_keyboard=True)
    bot.sendMessage(chat_id=id, text= back_to_menu_text, reply_markup=keyboard)
    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'VOLVER_MENU_VALIDACION', 'to_delete_message_id' : None } })

# VOLVER_MENU_VALIDACION
def back_menu_validation(id, bot, mycol, message, result):
    # No estamos desarrollando un item
    if not result['active_item']:
        if message[3:] == 'Si':
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU' } })
        elif message[3:] == 'No':
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'DIALOGO' } })
        else:
            bot.sendMessage(chat_id=id, text='No te estoy entendiendo. Intenta usar los botones de abajo.')
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'VOLVER_MENU' } })
    # Estamos dentro de un item y el usuario desea volver al menu de navegación
    else:
        if message[3:] == 'Si':
            second_attempt = False
            items_list = result['items_list']
            try:
                second_attempt = items_list[0]['second_attempt']
            except:
                pass
            items_list = result['items_list']
            actual_item = items_list[0]
            # Se manda la respuesta omitida o incorrecta
            task_user_instance_id = result['task']['task_user_instance_id']
            item_id = actual_item['id']
            choice_id = None
            try:
                choice_id = actual_item['user_choice_id']
            except:
                pass
            attempt = 2
            item_start_time = actual_item["item_start_time"]
            item_end_time = datetime.datetime.now()

            response_time_seconds = (item_end_time - item_start_time).total_seconds()
            url = 'http://localhost:3000/api/chatbot/v1/user_responses/'
            header = {'Authorization': 'Bearer ' + result['user_token']}
            data = {'task_user_instance_id' : task_user_instance_id, 'item_id' : item_id, 'choice_id' : choice_id, 'attempt' : attempt, 'response_time_seconds' : response_time_seconds}
            response = requests.post(url, data=data, headers=header)

            # Es el ultimo item de la tarea
            if len(result['items_list']) == 1:
                mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'TAREA_TERMINADA', "active_item" : False, 'to_delete_message_id' : [] } })
            else:
                items_list.pop(0)
                mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU', 'items_list' : items_list } })
        # No quiere salir y volvemos a mostrar el enunciado de la pregunta
        elif message[3:] == 'No':
            actual_item = result['items_list'][0]
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
            send_item_count = bot.sendMessage(chat_id=id, text="Pregunta. " + str(result['task']['total_items'] - len(result['items_list']) + 1) + " de " + str(result['task']['total_items']) +".", reply_markup=keyboard)

            to_delete_message_id = result["to_delete_message_id"]
            if to_delete_message_id == None:
                to_delete_message_id = [send_photo["message_id"], send_item_count["message_id"]]
            else:
                to_delete_message_id.append(send_photo["message_id"])
                to_delete_message_id.append(send_item_count["message_id"])

            mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM_SELECCIONADO' , "active_item" : True, "to_delete_message_id" : to_delete_message_id ,'items_list' : result['items_list']}})
            result = mycol.find_one( { 'id_telegram': id } )
        # No es una opcion valida
        else:
            bot.sendMessage(chat_id=id, text='Opcion invalida')
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'VOLVER_MENU' } })

# LOGROS
def menu_achievements(id, bot, mycol, message, result):
    # API - Consulta de todos los logros que tiene el alumno
    # Se envia:
    # - user_token
    # - id_group
    # Se recibe
    # Lista con los logros mostrados mas abajo
    """
    DATOS TEMPORALES
    """
    user_token = result['user_token']
    id_group = result['group']['id_group']
    tasks_hashtable = {
                        1 : { 'name' : 'Tarea completada', 'points' : 20, 'achievement_descriptions' : ['descripcion A', 'descripcion B'], 'achievement_pictures' : ["https://i1.theportalwiki.net/img/0/01/Achievement_Aperture_Science.png", "https://i1.theportalwiki.net/img/9/97/Achievement_Basic_Science.png"]},
                        2 : { 'name' : 'Tarea completada B', 'points' : 50, 'achievement_descriptions' : ['descripcion C'], 'achievement_pictures' : ["https://i1.theportalwiki.net/img/0/0e/Achievement_Rocket_Science.png"]},
                        3 : { 'name' : 'Tarea completada C', 'points' : 90, 'achievement_descriptions' : ['descripcion D', 'descripcion E', 'descripcion F'], 'achievement_pictures' : ["https://i1.theportalwiki.net/img/3/3d/Achievement_Fratricide.png", "https://i1.theportalwiki.net/img/a/ac/Achievement_Friendly_Fire.png", "https://i1.theportalwiki.net/img/0/08/Achievement_Fruitcake.png"]},
                        4 : { 'name' : 'Tarea completada D', 'points' : 0, 'achievement_descriptions' : [], 'achievement_pictures' : [] }
                      }
    """
    DATOS TEMPORALES
    """

    if tasks_hashtable == None:
        bot.sendMessage(chat_id=id, text= 'No tienes logros')
    else:
        for task in tasks_hashtable.keys():
            bot.sendMessage(chat_id=id, text= "* Tarea: " + tasks_hashtable[task]['name'] + "*" , parse_mode=telegram.ParseMode.MARKDOWN)
            bot.sendMessage(chat_id=id, text= "Puntos Obtenidos: " + str(tasks_hashtable[task]['points']))

            if len(tasks_hashtable[task]['achievement_descriptions']) == 0:
                bot.sendMessage(chat_id=id, text= "No obtuviste logros en esta tarea. ")
            else:
                bot.sendMessage(chat_id=id, text= "Logros: ")
                for achievement in range(len(tasks_hashtable[task]['achievement_descriptions'])):
                    bot.sendPhoto(chat_id=id, photo= tasks_hashtable[task]['achievement_pictures'][achievement])
                    bot.sendMessage(chat_id=id, text= tasks_hashtable[task]['achievement_descriptions'][achievement])
    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'VOLVER_MENU' } })

# PERFIL
def menu_profile(id, bot, mycol, message, result):
    bot.sendMessage(chat_id=id, text= 'FALTA POR DISCUTIR')
    bot.sendMessage(chat_id=id, text= str(result['user_name']) + " " + str(result['user_lastname']))
    bot.sendMessage(chat_id=id, text= str(result['user_email']))
    mycol.update( { 'id_telegram': id }, { '$set': { 'state' : 'VOLVER_MENU' } })

# MENU_SOLICITUD_AYUDA
def menu_help_request(id, bot, mycol, message, result):
    keyboard_array = [[emoji_correct + ' Si', emoji_incorrect + ' No']]
    keyboard = ReplyKeyboardMarkup(keyboard_array,  resize_keyboard=True, one_time_keyboard=True)
    bot.sendMessage(chat_id=id, text= "¿Quieres mandar una pregunta a un profesor?", reply_markup=keyboard)
    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU_SOLICITUD_AYUDA_VALIDACION' } })

# MENU_SOLICITUD_AYUDA_VALIDACION
def menu_help_request_validation(id, bot, mycol, message, result):
    if message[3:] == 'Si':
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU_SOLICITUD_AYUDA_MENSAJE' } })
    elif message[3:] == 'No':
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU' } })

# MENU_SOLICITUD_AYUDA_MENSAJE
def menu_help_request_message(id, bot, mycol, message, result):
    bot.sendMessage(chat_id=id, text= "Escribe el mensaje que quieres enviar")
    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU_SOLICITUD_AYUDA_ENVIAR'} })

# MENU_SOLICITUD_AYUDA_ENVIAR
def menu_help_request_send(id, bot, mycol, message, result):
    url = 'http://localhost:3000/api/chatbot/v1/user_help_requests'
    header = {'Authorization': 'Bearer ' + result['user_token']}
    data = {'group_id' : result['group']['id_group'], 'request_message' : message}

    response = requests.post(url, data=data, headers=header)

    if response.status_code == 200:
        bot.sendMessage(chat_id=id, text= "Mensaje enviado satisfactoriamente")
    else:
        bot.sendMessage(chat_id=id, text= "Error al enviar mensaje")

    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU' } })

# MENU_RESPUESTAS_RECIBIDAS
def menu_answers_received(id, bot, mycol, message, result):
    # Se crea el task_user_instance_id si no existe
    url = 'http://localhost:3000/api/chatbot/v1/user_help_requests/' + str(result['group']['id_group'])
    header = {'Authorization': 'Bearer ' + result['user_token']}
    response = requests.get(url, headers=header)

    if response.status_code == 200:
        response_json = json.loads(response.text)
        if len(response_json) == 0:
            bot.sendMessage(chat_id=id, text='No hay mensajes')
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU'}})
        else:
            actual_number = 0
            for incoming_message in response_json:
                actual_number +=1
                if "help_message_response" in incoming_message.keys():
                    if incoming_message["viewed"] == False:
                        bot.sendMessage(chat_id=id, text= str(actual_number) + ". " + emoji_red_light + " " + str(incoming_message["help_message"]) + " [ITEM]")
                    else:
                        bot.sendMessage(chat_id=id, text=str(actual_number) + ". " + str(incoming_message["help_message"]) + " [ITEM]")
                else:
                    if incoming_message["viewed"] == False:
                        bot.sendMessage(chat_id=id, text= str(actual_number) + ". " +emoji_red_light + " " + str(incoming_message["request_message"]) + " [MENU]")
                    else:
                        bot.sendMessage(chat_id=id, text=str(actual_number) + ". " + str(incoming_message["request_message"]) + " [MENU]")

            keyboard_array = []
            row_message = []
            for message_number in range(1, actual_number + 1):
                stored = False
                row_message.append(str(message_number))
                if message_number % 5 == 0:
                    keyboard_array.append(row_message)
                    row_message = []
                    stored = True
                if message_number == actual_number and stored == False:
                    keyboard_array.append(row_message)

            keyboard_array.append([emoji_run_girl + " Salir"])
            keyboard = ReplyKeyboardMarkup(keyboard_array,  one_time_keyboard=True)
            bot.sendMessage(chat_id=id, text= 'Selecciona el mensaje que quieras leer', reply_markup=keyboard)


    else:
        bot.sendMessage(chat_id=id, text='Error al obtener los mensajes')
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU'}})
