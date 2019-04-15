# -*- coding: utf-8 -*-
import json
import requests
from telegram import KeyboardButton, ReplyKeyboardMarkup

from emojis import *

# Ingreso a la base de datos
def database_insert(id, bot, mycol, message, result):
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
                "answers_received" : None,
                "to_delete_message_id" : None,
                "last_interaction_time" : None,
                "active_item" : None
            }
        ]
    )

# INGRESO
def session_ingress(id, bot, mycol, message, result):
    bot.sendMessage(id, 'Bienvenide ' + str(result['user_name']))
    mycol.update( { 'id_telegram' : id }, { '$set': { 'state': 'GRUPO' } })

# CERRAR_SESION
def close_session(id, bot, mycol, message, result):
    keyboard_array = [[emoji_correct + ' Si', emoji_incorrect + ' No']]
    keyboard = ReplyKeyboardMarkup(keyboard_array,  resize_keyboard=True, one_time_keyboard=True)
    bot.sendMessage(chat_id=id, text= '¿Seguro que quieres cerrar sesion?', reply_markup=keyboard)
    mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'CERRAR_SESION_PREGUNTA' } })

# CERRAR_SESION_PREGUNTA
def close_session_question(id, bot, mycol, message, result):
    if message[3:] == 'Si':
        bot.sendMessage(chat_id=id, text= 'Nos vemos pronto')
        mycol.delete_one({ 'id_telegram' : id })
    else:
        mycol.update( { 'id_telegram' : id }, { '$set': { 'state' : 'VOLVER_MENU' } })
