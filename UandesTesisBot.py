# -*- coding: utf-8 -*-

import requests
import apiai, codecs, json
import telegram
import pymongo
from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import *
import datetime
import json

from emojis import *
from credentials import *

# [States]
# AUTENTIFICACION_MENU: Se ofrece que campo desea ingresar para autentificarse
# AUTENTIFICACION_VALIDAR_MENU: Se valida la opcion ingresada por el usuario
# AUTENTIFICACION_TOKEN: Espera de que se ingrese el token de autentificación
# AUTENTIFICACION_VALIDAR_TOKEN: Se valida que el token ingresado sea correcto, en caso contrario vuelve a estado MENU_TOKEN_MAIL
# AUTENTIFICACION_MAIL: Se solicita el correo del alumno.
# AUTENTIFICACION_ENVIAR_MAIL: Se envia un mensaje con el token al correo del usuario. Se da feedback en caso que no exista en el sistema
# INGRESO: Se da información al usuario al momento de iniciar sesion
# CONTEXTO: Se informa al usuario sobre el contexto en el que estaba trabajando
# CONTEXTO_VALIDAR: Se valida la respuesta ingresada por el alumno
# GRUPO: Se da la opcion de elegir el grupo activo en que esta el alumno
# GRUPO_SELECCIONADO: Se valida la opcion de grupo ingresado por el alumno
# MENU: Se muestra elMENU_TOKEN_MAIL menu principal del bot
# MENU_SELECCIONADO: Se valida la opcion del menu ingresado por el alumno
# TAREAS: Muestra una lista de las tareas activas
# TAREA_SELECCIONADA: Se valida que la tarea ingresada sea correcta
# TAREA_TERMINADA: Se da informacion al usuario sobre la tarea terminada
# LOGROS: Muestra una lista con los logros desbloqueados y los que faltaron por desbloquear
# PERFIL: Muestra la informacion del perfil del alumno
# AYUDA_MENU: - POR DISCUTIR -
# CAMBIAR_GRUPO: Se vuelve a la opcion de GRUPO
# CERRAR_SESION: Se cierra la sesion del usuario
# DIALOGO: Estado en que se puede hablar abiertamente con el bot
# VOLVER_MENU: Se pregunta al usuario si desea volver al menu principal
# ITEM: Se solicita al backend la informacion de todos los items
# ITEM_DESPLEGAR_INFORMACION: Se despliega informacion del item en el chat (Este puede ser a partir de una tarea pendiente o elegida recien)
# ITEM_SELECCIONADO: Se valida la opcion ingresada por el alumno
# ITEM_SELECCIONADO_AYUDA: Se despliega el feedback ingresado por el profesor en caso de existir
# ITEM_SOLICITUD_SELECCIONADO_AYUDA: El alumno se equivoco 2 veces en un item, por lo que se pregunta si desea mandar una solicitud de ayuda a un profesor
# ITEM_SOLICITUD_AYUDA_VALIDACION: Se valida la respuesta del alumno sobre la solicitud de ayuda sobre un item
# ITEM_SOLICITUD_AYUDA_MENSAJE: El alumno escribe el mensaje de ayuda
# ITEM_SOLICITUD_AYUDA_ENVIAR: Se envia el mensaje de ayuda al profesor


#Telegram Connection
bot_updater = Updater(CLIENT_TELEGRAM_ACCESS_TOKEN)

#APIAI Connection
ai = apiai.ApiAI(CLIENT_APIAI_ACCESS_TOKEN)

# Database Connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["chatbot_development"]
mycol = db["user_context"]

print "Bot iniciado en Telegram"

def start_callback(bot, update):
    update.message.reply_text("Hola. Escribeme cualquier cosa para continuar")

# Interaccion con el bot en Telegram
def listener(bot, update):
    id = update.message.chat_id
    message = update.message.text

    print ("ID: " + str(id) + " message: " + message)
    result = mycol.find_one( { 'id_telegram': id } )

    if result == None:
        # Se ingresa el usuario a la base de datos
        mycol.insert(
            [
                {
                    "id_telegram" : id,
                    "user_token" : None,
                    "user_name" : None,
                    "user_lastname" : None,
                    "user_email" : None,
                    "state" : "AUTENTIFICACION_MENU",
                    "group" : {
                        "id_group" : None,
                        "name" : None,
                    },
                    "task" : {
                        "id_task" : None,
                        "name" : None
                    },
                    "groups_options" : None,
                    "tasks_options" : None,
                    "pending_task" : None,
                    "to_delete_message_id" : None,
                    "last_interaction_time" : None,
                    "active_item" : None
                }
            ]
        )
        result = mycol.find_one( { 'id_telegram': id } )

    if result['user_token'] == None:
        # Se verifica si existe un token de usuario asociado
        if result['state'] == 'AUTENTIFICACION_VALIDAR_MENU':
            if message == 'E-mail':
                mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'AUTENTIFICACION_EMAIL' } })
            elif message == 'Codigo':
                mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'AUTENTIFICACION_TOKEN' } })
            else:
                bot.sendMessage(chat_id=id, text= "No te estoy entendiendo. Intenta usar los botones de abajo.")
                mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'AUTENTIFICACION_MENU' } })
        result = mycol.find_one( { 'id_telegram': id } )

        if result['state'] == 'AUTENTIFICACION_MENU':
            keyboard_array = [['Codigo', 'E-mail']]
            keyboard = ReplyKeyboardMarkup(keyboard_array,  resize_keyboard=True, one_time_keyboard=True)
            bot.sendMessage(chat_id=id, text= 'Mira abajo, hay dos botones. Si tienes un código de acceso presiona "Código". En caso contrario, presiona "E-mail".', reply_markup=keyboard)
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'AUTENTIFICACION_VALIDAR_MENU' } })

        elif result['state'] == 'AUTENTIFICACION_EMAIL':
            bot.sendMessage(id, 'Ingresa tu correo.')
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state': 'AUTENTIFICACION_ENVIAR_EMAIL' } })

        elif result['state'] == 'AUTENTIFICACION_ENVIAR_EMAIL':
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

        elif result['state'] == 'AUTENTIFICACION_TOKEN':
            bot.sendMessage(id, 'Ingresa el código para ingresar.')
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state': 'AUTENTIFICACION_VALIDAR_TOKEN' } })

        elif result['state'] == 'AUTENTIFICACION_VALIDAR_TOKEN':
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

    if result['user_token'] != None:
        # Se actualiza el tiempo de interaccion
        last_time = result['last_interaction_time']
        actual_time = datetime.datetime.now()
        mycol.update( { 'id_telegram' : id }, { '$set': { 'last_interaction_time': datetime.datetime.now() } })


        # Se verifica que haya hablado anteriormente y que se encuentre dentro de un curso
        if last_time != None and result['group'] != None:
            # Paso mas de una hora
            if  ((actual_time - last_time).total_seconds() / 60) > 60:
                bot.sendMessage(id, 'Ha pasado un buen rato desde que conversamos por última vez ' + str(result['user_name']))
                mycol.update( { 'id_telegram' : id }, { '$set': { 'state': 'CONTEXTO' } })
            # Paso mas de 15 minutos
            elif ((actual_time - last_time).total_seconds() / 60) > 15:
                bot.sendMessage(id, 'Han pasado más de 15 minutos desde que hablamos ' + str(result['user_name']))
                mycol.update( { 'id_telegram' : id }, { '$set': { 'state': 'CONTEXTO' } })
        result = mycol.find_one( { 'id_telegram': id } )
        # Se valida la respuesta del alumno
        if result['state'] == 'CONTEXTO_VALIDAR':
            if message[3:] == 'Si':
                mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM' } })
            else:
                mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU' } })

        # Se informa al usuario el contexto en el que se encuentra
        if result['state'] == 'CONTEXTO':
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
            result = mycol.find_one( { 'id_telegram': id } )

        # Se saluda al usuario al ingresar por primera vez en el sistema
        if result['state'] == 'INGRESO':
            bot.sendMessage(id, 'Bienvenide ' + str(result['user_name']))
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state': 'GRUPO' } })
            result = mycol.find_one( { 'id_telegram': id } )

        # Se valida el curso seleccionado por el alumno
        if result['state'] == 'GRUPO_SELECCIONADO':
            groups_hashtable = json.loads(result["groups_options"])
            if message not in groups_hashtable.values():
                bot.sendMessage(chat_id=id, text='No te estoy entendiendo. Intenta usar los botones de abajo.')
                mycol.update( { 'id_telegram' : id }, { '$set': { 'state': 'GRUPO' }} )
            else:
                id_group = 0
                for identifier in groups_hashtable.keys():
                    if groups_hashtable[identifier] == message:
                        id_group = identifier
                bot.sendMessage(chat_id=id, text='Bienvenido al curso "' + str(message) + '". Puedes comenzar a practicar presionando “Tareas”. Mira el menú para otras opciones.')
                mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU', 'group' : { 'id_group' : int(id_group), 'name' : str(message) }}})
            result = mycol.find_one( { 'id_telegram': id } )

        # Validacion de la opcion seleccionada del menu de navegacion
        if result['state'] == 'MENU_SELECCIONADO':
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
                mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'AYUDA_MENU' } })
            elif message[3:] == 'Cambiar ramo':
                mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'CAMBIAR_GRUPO' } })
            elif message[3:] == 'Cerrar Sesion':
                mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'CERRAR_SESION' } })
            else:
                selected_menu_option = False

            if not selected_menu_option:
                mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'DIALOGO'}})
            result = mycol.find_one( { 'id_telegram': id } )

        # Se valida que la tarea seleccionada sea correcta y se comienza con el item
        if result['state'] == 'TAREA_SELECCIONADA':
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
            result = mycol.find_one( { 'id_telegram': id } )

        # Opciones del Menu de navegación
        if result['state'] == 'ITEM_SELECCIONADO':
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
            result = mycol.find_one( { 'id_telegram': id } )

        # Se valida la respuesta del alumno sobre la solicitud de ayuda en un item
        if result['state'] == 'ITEM_SOLICITUD_AYUDA_VALIDACION':
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
            result = mycol.find_one( { 'id_telegram': id } )

        # El alumno escribe el mensaje de ayuda sobre el item actual
        if result['state'] == 'ITEM_SOLICITUD_AYUDA_MENSAJE':
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
        # Se envia el mensaje de ayuda al profesor
        elif result['state'] == 'ITEM_SOLICITUD_AYUDA_ENVIAR':
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
            result = mycol.find_one( { 'id_telegram': id } )

        # Se pregunta al alumno si desea mandar una solicitud de ayuda a un profesor
        if result['state'] == 'ITEM_SOLICITUD_AYUDA':
            keyboard_array = [[emoji_correct + ' Si', emoji_incorrect + ' No']]
            keyboard = ReplyKeyboardMarkup(keyboard_array,  resize_keyboard=True, one_time_keyboard=True)
            bot.sendMessage(chat_id=id, text= "¿Quieres mandar una pregunta sobre este item a un profesor?", reply_markup=keyboard)
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'ITEM_SOLICITUD_AYUDA_VALIDACION' } })
            result = mycol.find_one( { 'id_telegram': id } )

        # Se entrega el feedback al alumno
        if result['state'] == 'ITEM_SELECCIONADO_AYUDA':
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
            result = mycol.find_one( { 'id_telegram': id } )

        # Se solicita la informacion de los items al backend
        if result['state'] == 'ITEM':
            task_user_instances_id = result['task']['task_user_instance_id']
            token = result['user_token']
            url = 'http://localhost:3000/api/chatbot/v1/task_user_instances/' + str(task_user_instances_id)
            header = {'Authorization': 'Bearer ' + token}
            response = requests.get(url, headers=header)
            items_list = []
            print "paso por aca"
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

            result = mycol.find_one( { 'id_telegram': id } )

        # Se muestra la informacion del item al alumno
        if result['state'] == 'ITEM_DESPLEGAR_INFORMACION':
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
            result = mycol.find_one( { 'id_telegram': id } )

        elif result['state'] == 'TAREAS':
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

        elif result['state'] == 'LOGROS':
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

        elif result['state'] == 'PERFIL':
            bot.sendMessage(chat_id=id, text= 'FALTA POR DISCUTIR')
            bot.sendMessage(chat_id=id, text= str(result['user_name']) + " " + str(result['user_lastname']))
            bot.sendMessage(chat_id=id, text= str(result['user_email']))
            mycol.update( { 'id_telegram': id }, { '$set': { 'state' : 'VOLVER_MENU' } })
        elif result['state'] == 'AYUDA_MENU':
            bot.sendMessage(chat_id=id, text= 'ayuda menu')
            bot.sendMessage(chat_id=id, text= 'FALTA POR DISCUTIR')
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'VOLVER_MENU' } })
        elif result['state'] == 'CAMBIAR_GRUPO':
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'GRUPO' , 'group' : None} })
        elif result['state'] == 'CERRAR_SESION':
            keyboard_array = [[emoji_correct + ' Si', emoji_incorrect + ' No']]
            keyboard = ReplyKeyboardMarkup(keyboard_array,  resize_keyboard=True, one_time_keyboard=True)
            bot.sendMessage(chat_id=id, text= '¿Seguro que quieres cerrar sesion?', reply_markup=keyboard)
            mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'CERRAR_SESION_PREGUNTA' } })
        elif result['state'] == 'CERRAR_SESION_PREGUNTA':
            if message[3:] == 'Si':
                bot.sendMessage(chat_id=id, text= 'Nos vemos pronto')
                mycol.delete_one({ 'id_telegram' : id })
            else:
                mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'VOLVER_MENU' } })
        result = mycol.find_one( { 'id_telegram': id } )

        # Dialogo abierto
        if result['state'] == 'DIALOGO':
            # Se prepara la solicitud a API.ai
            req = ai.text_request()
            req.query = message

            # Se recibe la respuesta de la API
            response = req.getresponse()
            response=json.loads(response.read())

            if response['result']['fulfillment']['speech'] == 'ERROR':
                bot.sendMessage(chat_id=id, text='No entendi el mensaje. ')
                mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'VOLVER_MENU' } })
            else:
                command = str(response['result']['metadata']['intentName'])
                text = str(response['result']['fulfillment']['speech'])
                bot.sendMessage(chat_id=id, text=text)
                if command in ['MENU', 'LOGROS', 'PERFIL']:
                    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : command } })
                else:
                    if command == 'HORA':
                        time = str(datetime.datetime.now().strftime("%I:%M%p de %B %d del %Y"))
                        bot.sendMessage(chat_id=id, text=time)

            result = mycol.find_one( { 'id_telegram': id } )

        if result['state'] == 'VOLVER_MENU_VALIDACION':
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
        result = mycol.find_one( { 'id_telegram': id } )

        # Pregunta al usuario si desea volver al menu de navegacion
        if result['state'] == 'VOLVER_MENU':
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

        # Se da informacion de los resultados de la tarea
        if result['state'] == 'TAREA_TERMINADA':
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
            result = mycol.find_one( { 'id_telegram': id } )

        # Selección del ramo para desarrollar las tareas
        if result['state'] == 'GRUPO':
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

        # Menu de navegación
        if result['state'] == 'MENU':
            """
            Opciones de menu:
            - (1): Continuar la ultima tarea visitada (En caso de haber)
            - (2): Ver el listado de tareas disponibles
            - (3): Ver logros
            - (4): Ver perfil propio
            - (5): Solicitar ayuda
            - (6): Cambiar el grupo ("ramo" actual)
            - (7): Cerrar Sesion
            """
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
                keyboard_array = [[emoji_back + ' Continuar tarea pendiente'],[emoji_task + ' Tareas'], [emoji_books + ' Cambiar ramo', emoji_run_girl + ' Cerrar Sesion']]
                # keyboard_array = [[emoji_back + ' Continuar tarea pendiente'],[emoji_task + ' Tareas'], [emoji_medal + ' Logros', emoji_nerd + ' Perfil'], [emoji_hand + ' Solicitar ayuda'], [emoji_books + ' Cambiar ramo', emoji_run_girl + ' Cerrar Sesion']]
            else:
                keyboard_array = [[emoji_task + ' Tareas'], [emoji_books + ' Cambiar ramo', emoji_run_girl + ' Cerrar Sesion']]
                # keyboard_array = [[emoji_task + ' Tareas'], [emoji_medal + ' Logros', emoji_nerd + ' Perfil'], [emoji_hand + ' Solicitar ayuda'], [emoji_books + ' Cambiar ramo', emoji_run_girl + ' Cerrar Sesion']]

            mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'MENU_SELECCIONADO' } })

            keyboard = ReplyKeyboardMarkup(keyboard_array,  one_time_keyboard=True)
            bot.sendMessage(chat_id=id, text= '- Menu Principal -', reply_markup=keyboard)
            result = mycol.find_one( { 'id_telegram': id } )


# Funcionamiento del Bot
listener_handler = MessageHandler(Filters.text, listener)
dispatcher = bot_updater.dispatcher

dispatcher.add_handler(CommandHandler("start", start_callback))
dispatcher.add_handler(listener_handler)

 # Comienza el Bot
bot_updater.start_polling()
bot_updater.idle()


# buscar en las cajas las cosas
# Tarea de vision
# leer lo de facebook
# tintoreria
# api log in
# redactar carta al consejo
