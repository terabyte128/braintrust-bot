import json

from django.http.response import HttpResponse
from django.shortcuts import render
import telegram
import requests

# Create your views here.

API_KEY = "167262782:AAFZohXUGULwNp_0x8Bh-s_AWkEaT0t0VLQ"

bot = telegram.Bot(token=API_KEY)


def set_webhook(request):
    if request.GET.get('url'):
        bot.setWebhook(request.GET.get('url'))
        return HttpResponse("Webhook successfully set to %s" % request.GET.get('url'))
    else:
        return HttpResponse("Failed to set webhook")


def webhook(request):
    update = json.loads(request.body)
    chat_id = update.message.chat.id

    bot.sendMessage(chat_id, request.body)
    return HttpResponse("success?")
