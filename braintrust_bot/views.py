import json

from django.http.response import HttpResponse
import telegram
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

API_KEY = "167262782:AAFZohXUGULwNp_0x8Bh-s_AWkEaT0t0VLQ"

bot = telegram.Bot(token=API_KEY)


def set_webhook(request):
    if request.GET.get('url'):
        bot.setWebhook(request.GET.get('url'))
        return HttpResponse("Webhook successfully set to %s" % request.GET.get('url'))
    else:
        return HttpResponse("Failed to set webhook")


@csrf_exempt
def webhook(request):
    try:
        update = json.loads(request.body.decode('utf-8'))
        print("json = " + str(update))
    except Exception as e:
        print(e)

    return HttpResponse("success?")
