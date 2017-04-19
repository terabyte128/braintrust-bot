import json
import random
import threading
import traceback

import telegram
import time
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http.response import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from braintrust_bot.memes import meme_ids
import requests

# Create your views here.
from braintrust_bot.models import ChatMember, QuoteChat, QuoteStorage, ChatGroup, ChatGroupMember
from django_braintrust_bot.settings import API_KEY

# initialize the bot for all views
bot = telegram.Bot(token=API_KEY)


# This page doesn't do much, just verify that the bot is working as expected
@login_required
def index(request):
    chats = ChatGroup.objects.all()

    context = {
        chats: chats
    }

    return render(request, 'braintrust_bot/index.html', context)


def sign_out(request):
    logout(request)
    return HttpResponse("Signed out successfully.")


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
            update = json.loads(request.body.decode('utf-8'))

            if 'message' in update:

                chat_id = update['message']['chat']['id']
                text = update['message']['text']

                # if the message starts with a /, it's a command, so handle it
                if text[0] == "/":
                    send_command(text[1:].split(" "), chat_id, update['message']['from']['username'], update)

                # otherwise, do nothing
                else:
                    pass

            elif 'inline_query' in update:
                pass

            # request was OK, so return 200
            return HttpResponse(status=200)


        # something went wrong with processing the request
        except Exception:
            print("An exception occurred.")
            print(traceback.format_exc())
            return

    else:
        # otherwise, unauthorized
        return HttpResponse(status=401)


def handle_inline(query, chat_id, sender):
    pass


# function to handle all commands sent to the bot
def send_command(args, chat_id, sender, update):

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
            bot.sendMessage(chat_id=chat_id, text="%s was successfully added to the global chat group." % member_str)
        except IntegrityError:
            bot.sendMessage(chat_id=chat_id, text="%s is already in the global chat group." % member_str)

    # remove command - remove a user
    elif command == "remove" and args[1]:
        # split off @ at beginning if necessary
        member_str = args[1][1:] if args[1][0] == "@" else args[1]

        # try and delete user unless they don't exist
        try:
            member = ChatMember.objects.get(username=member_str)
            member.delete()
            bot.sendMessage(chat_id=chat_id, text="%s was successfully deleted from the global chat group." % member_str)
        except ChatMember.DoesNotExist:
            bot.sendMessage(chat_id=chat_id, text="%s is not in the global chat group." % member_str)

    # list command - list all users
    elif command == "members":
        users = ChatMember.objects.filter(chat_id=chat_id)
        formatted_users = [user.username for user in users]

        bot.sendMessage(chat_id=chat_id, text="Members in global chat group: %s" % (", ".join(formatted_users)))

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

    elif command == "sendquote" or command == "sq":

        print(update)

        # if it's a reply, then use the original message as the quote
        if 'reply_to_message' in update['message']:
            original_message = update['message']['reply_to_message']

            # if there's context (passed as the single argument) then add it
            if len(args) > 1:
                context = " ".join(args[1:])
            else:
                context = ""

            # this only really works if a message has an author and text
            if 'from' in original_message:
                author = original_message['from']['first_name']
            else:
                return

            if 'text' in original_message:
                quote = original_message['text']
            else:
                return

        # otherwise, try and parse the quote
        else:
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

    elif command == "getquote" or command == "gq":
        random_idx = random.randint(0, QuoteStorage.objects.filter(chat_id=chat_id).count() - 1)
        random_obj = QuoteStorage.objects.filter(chat_id=chat_id)[random_idx]

        quote = generate_quote(random_obj)

        bot.sendMessage(chat_id=chat_id, text=quote, parse_mode="HTML")

    elif command == "summon" or command == "braintrust" or command == "s":

        message_pieces = generate_summon(chat_id, update['message']['from']['username'],
                                         update['message']['from']['first_name'], " ".join(args[1:]))

        full_message = "%s\n%s" % (message_pieces[0], message_pieces[1])

        message = bot.sendMessage(chat_id=chat_id, text=full_message, parse_mode="HTML")

        # this is hacky and not a good idea
        time.sleep(0.1)

        # immediately edit the message
        bot.editMessageText(message_pieces[0], chat_id=chat_id, message_id=message.message_id, parse_mode="HTML")

    elif command == "listgroups" or command == "lg":
        groups = ChatGroup.objects.filter(chat_id=chat_id)
        if len(groups) != 0:
            m_text = "Groups in this chat: " + ", ".join([group.name for group in groups])
            bot.sendMessage(chat_id=chat_id, text=m_text)
        else:
            bot.sendMessage(chat_id=chat_id, text="No groups in this chat.")

    elif command == "newgroup" or command == "ng":
        try:
            name = args[1]
            try:
                # the name and chat ID must be unique together, otherwise a ValidationError will be raised
                group = ChatGroup(name=name, chat_id=chat_id)
                group.save()

                bot.sendMessage(chat_id=chat_id, text="Group saved successfully. Add new members with: "
                                                      "/addgroupmember %s [member name]" % name)
            except ValidationError:
                bot.sendMessage(chat_id=chat_id, text="This group already exists.")

        except IndexError:
            bot.sendMessage(chat_id=chat_id, text="Usage: /newgroup [group name]")

    elif command == "addgroupmember" or command == "agm":
        try:
            group_name = args[1]
            member_names = args[2:]

            try:
                # name and ID together will always be unique
                group = ChatGroup.objects.get(name=group_name, chat_id=chat_id)
                new_members = []
                already_there = []

                for member_name in member_names:
                    try:
                        member = ChatGroupMember(username=member_name, chat_group=group)
                        member.save()
                        new_members.append(member_name)
                    except ValidationError:
                        already_there.append(member_name)

                message_text = group_name + ":\n"
                if len(new_members) != 0:
                    message_text += "Added %s to group.\n" % ", ".join(new_members)
                if len(already_there) != 0:
                    message_text += "%s were already in group.\n" % ", ".join(already_there)

                bot.sendMessage(chat_id=chat_id, text=message_text)

            except ChatGroup.DoesNotExist:
                bot.sendMessage(chat_id=chat_id, text="This group does not exist. Create it with: /newgroup %s"
                                                      % group_name)

        except IndexError:
            bot.sendMessage(chat_id=chat_id, text="Usage: /addgroupmember [group name] [member name]")

    elif command == "removegroupmember" or command == "rgm":
        try:
            group_name = args[1]
            member_name = args[2]

            try:
                # name and ID together will always be unique
                group = ChatGroup.objects.get(name=group_name, chat_id=chat_id)

                try:
                    member = ChatGroupMember.objects.get(chat_group=group, username=member_name)
                    member.delete()
                except ChatGroupMember.DoesNotExist:
                    bot.sendMessage(chat_id=chat_id, text="%s is not a member of the %s group."
                                                          % (member_name, group_name))

            except ChatGroup.DoesNotExist:
                bot.sendMessage(chat_id=chat_id, text="This group does not exist. Create it with: /newgroup %s"
                                                      % group_name)

        except IndexError:
            bot.sendMessage(chat_id=chat_id, text="Usage: /removegroupmember [group name] [member name]")

    elif command == "messagegroup" or command == "mg":
        try:
            group_name = args[1]
            message = " ".join(args[2:])

            if len(message) == 0:
                raise IndexError

            try:
                # name and ID together will always be unique
                group = ChatGroup.objects.get(name=group_name, chat_id=chat_id)
                members = ChatGroupMember.objects.filter(chat_group=group)

                formatted_users = ["@" + user.username for user in members]

                message_text = "<strong>%s</strong>: %s\n\n%s" \
                           % (update['message']['from']['first_name'], message,
                              " ".join(formatted_users))

                # go go gadget send message!
                bot.sendMessage(chat_id=chat_id, text=message_text, parse_mode="HTML")

            except ChatGroup.DoesNotExist:
                bot.sendMessage(chat_id=chat_id, text="This group does not exist. Create it with: /newgroup %s"
                                                      % group_name)

        except IndexError:
            bot.sendMessage(chat_id=chat_id, text="Usage: /messagegroup [group name] [message]")

    elif command == "membersingroup" or command == "mig":
        try:
            group_name = args[1]

            try:
                # name and ID together will always be unique
                group = ChatGroup.objects.get(name=group_name, chat_id=chat_id)
                members = ChatGroupMember.objects.filter(chat_group=group)

                message = "Members in %s group: %s" % (group_name, ", ".join([member.username for member in members]))

                bot.sendMessage(chat_id=chat_id, text=message)

            except ChatGroup.DoesNotExist:
                bot.sendMessage(chat_id=chat_id, text="This group does not exist. Create it with: /newgroup %s"
                                                      % group_name)

        except IndexError:
            bot.sendMessage(chat_id=chat_id, text="Usage: /membersingroup [group name]")

    elif command == "removegroup" or command == "rg":
        try:
            group_name = args[1]

            try:
                # name and ID together will always be unique
                group = ChatGroup.objects.get(name=group_name, chat_id=chat_id)
                group.delete()

                bot.sendMessage(chat_id=chat_id, text="Group removed successfully.")

            except ChatGroup.DoesNotExist:
                bot.sendMessage(chat_id=chat_id, text="This group does not exist. Create it with: /newgroup %s"
                                                      % group_name)

        except IndexError:
            bot.sendMessage(chat_id=chat_id, text="Usage: /removegroup [group name]")

    elif command == "getmeme" or command == "gm":
        try:
            random_idx = random.randint(0, QuoteStorage.objects.filter(chat_id=chat_id).count() - 1)
            random_quote = QuoteStorage.objects.filter(chat_id=chat_id)[random_idx]

            meme_url = generate_meme(random_quote.text)
            bot.sendMessage(chat_id=chat_id, text=meme_url)

        # if there are no quotes, just give up
        except Exception as e:
            print(e)

    # otherwise it's not a real command :(
    else:
        bot.sendMessage(chat_id=chat_id, text="@%s: Command not found." % sender)


# returns an HTML-formatted quote
def generate_quote(quote):
    try:
        capitalized = quote.text[0].upper() + quote.text[1:]
    except IndexError:
        capitalized = quote.text[0].upper()

    text = "<i>\"%s\"</i>\n<strong> - %s %4d</strong>" % (capitalized, quote.author.title(),
                                                          quote.timestamp.year)
    if quote.context != "":
        text += " (%s)" % quote.context

    return text


def generate_meme(quote_text):
    try:
        capitalized = quote_text[0].upper() + quote_text[1:]
    except IndexError:
        capitalized = quote_text[0].upper()

    split_quote = capitalized.split()

    num_words = len(split_quote)

    # split the number of words in the quote in half
    size_first_half = int(num_words / 2)
    size_second_half = num_words - size_first_half

    first_half = " ".join(split_quote[0:size_first_half])
    second_half = " ".join(split_quote[size_first_half:num_words])

    random_meme = meme_ids[random.randint(0, len(meme_ids) - 1)]

    request = {
        'username': 'imgflip_hubot',
        'password': 'imgflip_hubot',
        'template_id': random_meme,
        'text0': first_half,
        'text1': second_half,
    }

    r = requests.post('https://api.imgflip.com/caption_image', data=request)

    return r.json()['data']['url']


def generate_summon(chat_id, sender_username, sender_name, message):
    # get users for group, except message sender
    users = ChatMember.objects.filter(chat_id=chat_id).exclude(username__iexact=sender_username)

    # format as list starting with @, required for tagging usernames
    formatted_users = ["@" + user.username for user in users]

    # send message as reply with comma-separated list of tagged users
    message_text = "<strong>%s</strong>: %s" % (sender_name, message)

    formatted_users_text = " ".join(formatted_users)
    return message_text, formatted_users_text


class SendSummonAsync(threading.Thread):
    def __init__(self, chat_id, sender_username, sender_first_name, message):
        threading.Thread.__init__(self)
        self.chat_id = chat_id
        self.sender_username = sender_username
        self.sender_first_name = sender_first_name
        self.message = message

    def run(self):
        message_pieces = generate_summon(self.chat_id, self.sender_username,
                                         self.sender_first_name, self.message)

        full_message = "%s\n\n%s" % (message_pieces[0], message_pieces[1])

        message = bot.sendMessage(chat_id=self.chat_id, text=full_message, parse_mode="HTML")

        # immediately edit the message
        bot.editMessageText(message_pieces[0], chat_id=self.chat_id, message_id=message.message_id)