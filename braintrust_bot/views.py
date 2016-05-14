import json
import random
import traceback

import telegram
from django.db import IntegrityError
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
from braintrust_bot.models import ChatMember, QuoteChat, QuoteStorage
from django_braintrust_bot.settings import API_KEY

# initialize the bot for all views
bot = telegram.Bot(token=API_KEY)


# This page doesn't do much, just verify that the bot is working as expected
def index(request):
    return HttpResponse("BrainTrust Bot 2.0")


# Set the webhook for the bot - should be disabled in production via urls.py
def set_webhook(request):
    if request.GET.get('url'):
        bot.setWebhook(request.GET.get('url'))
        return HttpResponse("Webhook successfully set to %s" % request.GET.get('url'))
    else:
        return HttpResponse("Failed to set webhook")


# Handle all webhook requests - Telegram cannot send csrf tokens, so disable this functionality
@csrf_exempt
def webhook(request):
    # only respond to request if the bot uses the correct API key (encoded in GET)
    if request.GET.get('API_KEY') == API_KEY:
        try:
            # try to load info from JSON request body
            update = json.loads(request.body.decode('utf-8'))
            chat_id = update['message']['chat']['id']
            text = update['message']['text']

            # if the message starts with a /, it's a command, so handle it
            if text[0] == "/":
                send_command(text[1:].split(" "), chat_id, update['message']['from']['username'])

            # otherwise, just send a reply with everyone tagged from the chat group
            else:
                # get users for group, except message sender
                users = ChatMember.objects.filter(chat_id=chat_id).exclude(username=update['message']['from']['username'])

                # format as list starting with @, required for tagging usernames
                formatted_users = ["@" + user.username for user in users]

                # send message as reply with comma-separated list of tagged users
                message_text = "<strong>%s</strong>: %s\n\n%s" \
                               % (update['message']['from']['first_name'], update['message']['text'],
                                  ", ".join(formatted_users))

                # go go gadget send message!
                bot.sendMessage(chat_id=chat_id, text=message_text, parse_mode="HTML")

        # catch all - probably bad practice
        except Exception:
            print("An exception occurred.")
            print(traceback.format_exc())

        # request was OK, so return 200
        return HttpResponse(status=200)
    else:
        # otherwise, unauthorized
        return HttpResponse(status=401)


# function to handle all commands sent to the bot
def send_command(args, chat_id, sender):

    # there might be @BrianTrustBot afterwards, so get rid of it if it exists
    command = args[0].split("@")[0]

    # add command - add a user
    if command == "add" and args[1]:
        # split off @ at beginning if necessary
        member_str = args[1][1:] if args[1][0] == "@" else args[1]

        # try and save user, unless they already exist in the db
        try:
            member = ChatMember(username=member_str, chat_id=chat_id)
            member.save()
            bot.sendMessage(chat_id=chat_id, text="@%s: %s was successfully added to the group." % (sender, member_str))
        except IntegrityError:
            bot.sendMessage(chat_id=chat_id, text="@%s: %s is already in the group." % (sender, member_str))

    # remove command - remove a user
    elif command == "remove" and args[1]:
        # split off @ at beginning if necessary
        member_str = args[1][1:] if args[1][0] == "@" else args[1]

        # try and delete user unless they don't exist
        try:
            member = ChatMember.objects.get(username=member_str)
            member.delete()
            bot.sendMessage(chat_id=chat_id, text="@%s: %s was successfully deleted from the group."
                                                     % (sender, member_str))
        except ChatMember.DoesNotExist:
            bot.sendMessage(chat_id=chat_id, text="@%s: %s is not in the group." % (sender, member_str))

    # list command - list all users
    elif command == "members":
        users = ChatMember.objects.filter(chat_id=chat_id)
        formatted_users = [user.username for user in users]

        bot.sendMessage(chat_id=chat_id, text="Members in group: %s" % (", ".join(formatted_users)))

    elif command == "quotes":
        if args[1] and (args[1] == "enable" or args[1] == "disable"):
            try:
                quote_chat = QuoteChat.objects.get(chat_id=chat_id)
            except QuoteChat.DoesNotExist:
                quote_chat = QuoteChat(chat_id=chat_id)

            quote_chat.quotes_enabled = (args[1] == "enable")
            quote_chat.save()
            bot.sendMessage(chat_id=chat_id, text="Quotes %s." % ("enabled" if quote_chat.quotes_enabled else "disabled"))
        else:
            bot.sendMessage(chat_id=chat_id, text="Usage: /quotes [enable/disable]")

    elif command == "sendquote":
        not_command = " ".join(args[1:])
        split = not_command.split(" && ")

        try:
            quote = split[0]
            author = split[1]
        except IndexError:
            bot.sendMessage(chat_id=chat_id, text='Usage: /sendquote quote && author [&& context]')
            return

        try:
            context = split[2]
        except IndexError:
            context = ""

        new_quote = QuoteStorage(chat_id=chat_id, text=quote, author=author, context=context)
        new_quote.save()
        bot.sendMessage(chat_id=chat_id, text="Quote saved successfully.")

    elif command == "getquote":
        random_idx = random.randint(0, QuoteStorage.objects.filter(chat_id=chat_id).count() - 1)
        random_obj = QuoteStorage.objects.filter(chat_id=chat_id)[random_idx]

        quote = generate_quote(random_obj)

        bot.sendMessage(chat_id=chat_id, text=quote, parse_mode="HTML")

    elif command == "summon" or command == "braintrust":
        # get users for group, except message sender
        users = ChatMember.objects.filter(chat_id=chat_id).exclude(username=update['message']['from']['username'])

        # format as list starting with @, required for tagging usernames
        formatted_users = ["@" + user.username for user in users]

        # send message as reply with comma-separated list of tagged users
        message_text = "<strong>%s</strong>: %s\n\n%s" \
                       % (update['message']['from']['first_name'], " ".join(args[1:]),
                          ", ".join(formatted_users))

        # go go gadget send message!
        bot.sendMessage(chat_id=chat_id, text=message_text, parse_mode="HTML")

    # otherwise it's not a real command :(
    else:
        bot.sendMessage(chat_id=chat_id, text="@%s: Command not found." % sender)


# returns an HTML-formatted quote
def generate_quote(quote):
    text = "<i>\"%s\"</i>\n<strong> - %s %4d</strong>" % (quote.text.capitalize(), quote.author.title(), quote.timestamp.year)
    if quote.context != "":
        text += " (%s)" % quote.context

    return text
