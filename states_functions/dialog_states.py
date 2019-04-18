# -*- coding: utf-8 -*-
import json
import datetime

# DIALOGO
def dialog(id, ai, bot, mycol, message, result):
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
