# -*- coding: utf-8 -*-

import pymongo
from telegram.ext import *
import datetime
import apiai, codecs

from credentials import *
from states_functions.group_states import *
from states_functions.item_states import *
from states_functions.authentication_states import *
from states_functions.task_states import *
from states_functions.context_states import *
from states_functions.menu_states import *
from states_functions.dialog_states import *

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
# VOLVER_MENU: Se pregunta al usuario si desea volver al menu principal
# TAREAS: Muestra una lista de las tareas activas
# TAREA_SELECCIONADA: Se valida que la tarea ingresada sea correcta
# TAREA_TERMINADA: Se da informacion al usuario sobre la tarea terminada
# MENU_RESPUESTAS_RECIBIDAS: Se muestran las respuestas hechas por los profesores a las preguntas del alumno tanto en item como generales al ramo.
# LOGROS: Muestra una lista con los logros desbloqueados y los que faltaron por desbloquear
# PERFIL: Muestra la informacion del perfil del alumno
# MENU_SOLICITUD_AYUDA: Se envia una pregunta sobre cualquier cosa dentro de un grupo en particular
# CAMBIAR_GRUPO: Se vuelve a la opcion de GRUPO
# CERRAR_SESION: Se cierra la sesion del usuario
# DIALOGO: Estado en que se puede hablar abiertamente con el bot
# ITEM: Se solicita al backend la informacion de todos los items
# ITEM_DESPLEGAR_INFORMACION: Se despliega informacion del item en el chat (Este puede ser a partir de una tarea pendiente o elegida recien)
# ITEM_SELECCIONADO: Se valida la opcion ingresada por el alumno
# ITEM_SELECCIONADO_AYUDA: Se despliega el feedback ingresado por el profesor en caso de existir
# ITEM_SOLICITUD_AYUDA: El alumno se equivoco 2 veces en un item, por lo que se pregunta si desea mandar una solicitud de ayuda a un profesor
# ITEM_SOLICITUD_AYUDA_VALIDACION: Se valida la respuesta del alumno sobre la solicitud de ayuda sobre un item
# ITEM_SOLICITUD_AYUDA_MENSAJE: El alumno escribe el mensaje de ayuda
# ITEM_SOLICITUD_AYUDA_ENVIAR: Se envia el mensaje de ayuda al profesor


#Telegram Connection
bot_updater = Updater(CLIENT_TELEGRAM_ACCESS_TOKEN_PRODUCTION)

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
        database_insert(id=id, bot=bot, mycol=mycol, message=message, result=result)
        result = mycol.find_one( { 'id_telegram': id } )

    # No existe un usuario asociado
    if result['user_token'] == None:
        authentication_flow(id=id, bot=bot, mycol=mycol, message=message, result=result)
        result = mycol.find_one( { 'id_telegram': id } )

    # Existe un usuario asociado
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
            context_validate(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        # Se informa al usuario el contexto en el que se encuentra
        if result['state'] == 'CONTEXTO':
            context(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        # Se saluda al usuario al ingresar por primera vez en el sistema
        if result['state'] == 'INGRESO':
            session_ingress(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        # Se valida el curso seleccionado por el alumno
        if result['state'] == 'GRUPO_SELECCIONADO':
            selected_group(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        # Validacion de la opcion seleccionada del menu de navegacion
        if result['state'] == 'MENU_SELECCIONADO':
            menu_selected(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        # Se valida que la tarea seleccionada sea correcta y se comienza con el item
        if result['state'] == 'TAREA_SELECCIONADA':
            task_selected(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        # Opciones del Menu de navegación
        if result['state'] == 'ITEM_SELECCIONADO':
            item_selected(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        # Se valida la respuesta del alumno sobre la solicitud de ayuda en un item
        if result['state'] == 'ITEM_SOLICITUD_AYUDA_VALIDACION':
            item_request_help_validation(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        # El alumno escribe el mensaje de ayuda sobre el item actual
        if result['state'] == 'ITEM_SOLICITUD_AYUDA_MENSAJE':
            item_request_help_message(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )
        # Se envia el mensaje de ayuda al profesor
        elif result['state'] == 'ITEM_SOLICITUD_AYUDA_ENVIAR':
            item_request_help_send(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        # Se pregunta al alumno si desea mandar una solicitud de ayuda a un profesor
        if result['state'] == 'ITEM_SOLICITUD_AYUDA':
            item_request_help(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        # Se entrega el feedback al alumno
        if result['state'] == 'ITEM_SELECCIONADO_AYUDA':
            item_selected_help(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        # Se solicita la informacion de los items al backend
        if result['state'] == 'ITEM':
            items(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        # Se muestra la informacion del item al alumno
        if result['state'] == 'ITEM_DESPLEGAR_INFORMACION':
            item_display_information(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        # Se muestran las respuestas a las preguntas hechas por el alumno en caso de haber
        if result['state'] == 'MENU_RESPUESTAS_RECIBIDAS':
            menu_answers_received(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        # Se envia el mensaje de ayuda al backend
        if result['state'] == 'MENU_SOLICITUD_AYUDA_ENVIAR':
            menu_help_request_send(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        # Se valida la respuesta ingresada por el alumno
        if result['state'] == 'MENU_SOLICITUD_AYUDA_VALIDACION':
            menu_help_request_validation(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        # Se solicita el mensaje de ayuda al alumno
        if result['state'] == 'MENU_SOLICITUD_AYUDA_MENSAJE':
            menu_help_request_message(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )
        # Se muestran las tareas disponibles
        elif result['state'] == 'TAREAS':
            tasks(id=id, bot=bot, mycol=mycol, message=message, result=result)
        # Se muestran los logros desbloqueados
        elif result['state'] == 'LOGROS':
            menu_achievements(id=id, bot=bot, mycol=mycol, message=message, result=result)
        # Se muestra la informacion del perfil
        elif result['state'] == 'PERFIL':
            menu_profile(id=id, bot=bot, mycol=mycol, message=message, result=result)
        # Se envia solicitud de ayuda general de un ramo en especifico
        elif result['state'] == 'MENU_SOLICITUD_AYUDA':
            menu_help_request(id=id, bot=bot, mycol=mycol, message=message, result=result)
        elif result['state'] == 'CAMBIAR_GRUPO':
            change_group(id=id, bot=bot, mycol=mycol, message=message, result=result)
        elif result['state'] == 'CERRAR_SESION':
            close_session(id=id, bot=bot, mycol=mycol, message=message, result=result)
        elif result['state'] == 'CERRAR_SESION_PREGUNTA':
            close_session_question(id=id, bot=bot, mycol=mycol, message=message, result=result)
        result = mycol.find_one( { 'id_telegram': id } )

        # Dialogo abierto
        if result['state'] == 'DIALOGO':
            dialog(id=id, ai=ai, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        if result['state'] == 'VOLVER_MENU_VALIDACION':
            back_menu_validation(id=id, bot=bot, mycol=mycol, message=message, result=result)
        result = mycol.find_one( { 'id_telegram': id } )

        # Pregunta al usuario si desea volver al menu de navegacion
        if result['state'] == 'VOLVER_MENU':
            back_menu(id=id, bot=bot, mycol=mycol, message=message, result=result)
        # Se da informacion de los resultados de la tarea
        if result['state'] == 'TAREA_TERMINADA':
            task_finished(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        # Selección del ramo para desarrollar las tareas
        if result['state'] == 'GRUPO':
            groups(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )

        # Menu de navegación
        if result['state'] == 'MENU':
            menu(id=id, bot=bot, mycol=mycol, message=message, result=result)
            result = mycol.find_one( { 'id_telegram': id } )


# Funcionamiento del Bot
listener_handler = MessageHandler(Filters.text, listener)
dispatcher = bot_updater.dispatcher

dispatcher.add_handler(CommandHandler("start", start_callback))
dispatcher.add_handler(listener_handler)

 # Comienza el Bot
bot_updater.start_polling()
bot_updater.idle()
