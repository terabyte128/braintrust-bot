import json
import telegram

from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError

# Create your views here.
from braintrust_bot.models import ChatMember

API_KEY = "167262782:AAFZohXUGULwNp_0x8Bh-s_AWkEaT0t0VLQ"

bot = telegram.Bot(token=API_KEY)


def set_webhook(request):
    if request.GET.get('url'):
        bot.setWebhook(request.GET.get('url'))
        return HttpResponse("Webhook successfully set to %s" % request.GET.get('url'))
    else:
        return HttpResponse("Failed to set webhook")

'''
{
   'update_id':130689848,
   'message':{
      'message_id':106,
      'from':{
         'first_name':'Sam',
         'id':147524383,
         'last_name':'Wolfson',
         'username':'SamWolfson'
      },
      'text':'fff',
      'chat':{
         'first_name':'Sam',
         'id':147524383,
         'last_name':'Wolfson',
         'username':'SamWolfson',
         'type':'private'
      },
      'date':1462522610
   }
}
'''


@csrf_exempt
def webhook(request):
    try:
        update = json.loads(request.body.decode('utf-8'))
        chat_id = update['message']['chat']['id']
        text = update['message']['text']

        if text[0] == "/":
            send_command(text[1:].split(" "), chat_id, update['message']['from']['username'])
        else:
            users = ChatMember.objects.filter(chat_id=chat_id).exclude(username=update['message']['from']['username'])

            formatted_users = ["@" + user.username for user in users]

            message_text = "%s called together the Brain Trust: %s" \
                           % (update['message']['from']['first_name'], ", ".join(formatted_users))

            bot.sendMessage(chat_id=chat_id, text=message_text, reply_to_message_id=update['message']['message_id'])

    except Exception as e:
        print("error: " + str(e))

    return HttpResponse()


def send_command(args, chat_id, sender):

    # there might be @BrianTrustBot afterwards
    command = args[0].split("@")[0]

    if command == "add" and args[1] != "":
        try:
            member = ChatMember(username=args[1], chat_id=chat_id)
            member.save()
            bot.sendMessage(chat_id=chat_id, text="@%s: %s was successfully added to the group." % (sender, args[1]))
        except IntegrityError:
            bot.sendMessage(chat_id=chat_id, text="@%s: %s is already in the group." % (sender, args[1]))

    elif command == "remove" and args[1] != "":
        try:
            member = ChatMember.objects.get(username=args[1])
            member.delete()
            bot.sendMessage(chat_id=chat_id, text="@%s: %s was successfully deleted from the group."
                                                     % (sender, args[1]))
        except ChatMember.DoesNotExist:
            bot.sendMessage(chat_id=chat_id, text="@%s: %s is not in the group." % (sender, args[1]))

    else:
        bot.sendMessage(chat_id=chat_id, text="@%s: Command not found." % sender)

