import json

import telegram
from django.db import IntegrityError
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
from braintrust_bot.models import ChatMember
from django_braintrust_bot.settings import API_KEY

bot = telegram.Bot(token=API_KEY)


def index(request):
    return HttpResponse("BrainTrust Bot 2.0")


def set_webhook(request):
    if request.GET.get('url'):
        bot.setWebhook(request.GET.get('url'))
        return HttpResponse("Webhook successfully set to %s" % request.GET.get('url'))
    else:
        return HttpResponse("Failed to set webhook")


@csrf_exempt
def webhook(request):
    if request.GET.get('API_KEY') == API_KEY:
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

        return HttpResponse(status=200)
    else:
        return HttpResponse(status=401)


def send_command(args, chat_id, sender):

    # there might be @BrianTrustBot afterwards
    command = args[0].split("@")[0]

    if command == "add" and args[1]:
        member_str = args[1][1:] if args[1][0] == "@" else args[1]

        try:
            member = ChatMember(username=member_str, chat_id=chat_id)
            member.save()
            bot.sendMessage(chat_id=chat_id, text="@%s: %s was successfully added to the group." % (sender, member_str))
        except IntegrityError:
            bot.sendMessage(chat_id=chat_id, text="@%s: %s is already in the group." % (sender, member_str))

    elif command == "remove" and args[1]:
        member_str = args[1][1:] if args[1][0] == "@" else args[1]

        try:
            member = ChatMember.objects.get(username=member_str)
            member.delete()
            bot.sendMessage(chat_id=chat_id, text="@%s: %s was successfully deleted from the group."
                                                     % (sender, member_str))
        except ChatMember.DoesNotExist:
            bot.sendMessage(chat_id=chat_id, text="@%s: %s is not in the group." % (sender, member_str))

    elif command == "members":
        users = ChatMember.objects.filter(chat_id=chat_id)
        formatted_users = [user.username for user in users]

        bot.sendMessage(chat_id=chat_id, text="Members in group: %s" % (", ".join(formatted_users)))

    else:
        bot.sendMessage(chat_id=chat_id, text="@%s: Command not found." % sender)

