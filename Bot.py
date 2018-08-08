import requests
import apiai, codecs, json
import telegram
from telegram.ext import *

#TesisUandesBot Telegram
mi_bot = telegram.Bot(token="589616531:AAEPqG7r11uRPSjKG4PivlDxLNTfDlZzUNk")
mi_bot_updater = Updater(mi_bot.token)

#APIAI Credentials
CLIENT_ACCESS_TOKEN = "<1a44566df094405fb8218c8ca8258e82>"
ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)

message = "hola"

# prepare API.ai request
req = ai.text_request()
req.query = message

# get response from API.ai
# response = req.getresponse()
response = req.getresponse()

print(response)
