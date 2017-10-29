import json
import random
import threading
import traceback

import telegram
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from braintrust_bot.memes import meme_ids
import requests

# Create your views here.
from braintrust_bot.models import ChatMember, QuoteChat, QuoteStorage, ChatGroup, ChatGroupMember, Photo, \
    EightBallAnswer, QuiplashPrompt, Alexa
from django_braintrust_bot.settings import API_KEY

# initialize the bot for all views
bot = telegram.Bot(token=API_KEY)


# This page doesn't do much, just verify that the bot is working as expected
@login_required
def index(request):
    context = {
        'alexas': Alexa.objects.filter(chat=None),
        'chats': QuoteChat.objects.all()
    }

    if request.method == "POST":
        alexa_id = request.POST.get('alexa_id')
        chat_id = request.POST.get('chat_id')

        alexa = Alexa.objects.get(id=alexa_id)
        chat = QuoteChat.objects.get(id=chat_id)

        if alexa and chat:
            alexa.chat = chat
            alexa.save()

            context['success'] = 'Your Alexa was updated.'
        else:
            context['error'] = 'Failed to update Alexa.'

    return render(request, 'braintrust_bot/index.html', context)

@csrf_exempt
def get_quote_alexa(request):
    body = json.loads(request.body)

    alexa_user_id = body['alexa_user_id']

    if not alexa_user_id:
        return JsonResponse({
            'text': 'The format of your request is incorrect.'
        })

    try:
        alexa = Alexa.objects.get(device_user_id=alexa_user_id)
    except Alexa.DoesNotExist:
        alexa = None

    if not alexa or alexa.chat is None:

        if not alexa:  # create a new object if we don't have one
            alexa = Alexa.objects.create(device_user_id=alexa_user_id)
            alexa.save()

        return JsonResponse({
            'text': 'You need to register your Alexa device.'
        })

    else:
        random_idx = random.randrange(0, QuoteStorage.objects.filter(chat_id=alexa.chat.chat_id).count())
        quote = QuoteStorage.objects.filter(chat_id=alexa.chat.chat_id)[random_idx]

        try:
            capitalized = quote.text[0].upper() + quote.text[1:]
        except IndexError:
            capitalized = quote.text[0].upper()

        return JsonResponse({
            'text': '<emphasis>%s</emphasis><break time="500ms"/>%s %4d' % (capitalized, quote.author.title(),
                                                                            quote.timestamp.year)
        })


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

                sender = ""

                if 'first_name' in update['message']['from']:
                    sender += update['message']['from']['first_name']

                if 'last_name' in update['message']['from']:
                    sender += " " + update['message']['from']['last_name']

                # we know how to process messages, and photos
                if 'text' in update['message']:
                    text = update['message']['text']

                    if text[0] == "/":
                        send_command(text[1:].split(" "), chat_id, update['message']['from']['username'], update,
                                     sender)

                # deal with photos separately
                elif 'photo' in update['message']:
                    photo_things = update['message']['photo']

                    caption = update['message']['caption'] if 'caption' in update['message'] else ""

                    largest_photo = None

                    # find the biggest photo ID
                    for photo in photo_things:
                        if largest_photo is not None:
                            if photo['file_size'] > largest_photo['file_size']:
                                largest_photo = photo
                        else:
                            largest_photo = photo

                    largest_photo_id = largest_photo['file_id']

                    add_photo(chat_id, sender, caption, largest_photo_id, update['message']['from']['username'])

                # otherwise, delete all unconfirmed photos
                else:
                    Photo.objects.filter(sender=sender, confirmed=False).order_by('-timestamp')
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


def add_photo(chat_id, sender, caption, photo_id, username):
    photo = Photo(chat_id=chat_id, sender=sender, caption=caption, photo_id=photo_id, sender_username=username)
    photo.save()


# function to handle all commands sent to the bot

# sender is the sender's NAME
def send_command(args, chat_id, sender_username, update, sender):
    # there might be @BrianTrustBot afterwards, so get rid of it if it exists
    command = args[0].split("@")[0]

    last_photo = Photo.objects.filter(sender_username=sender_username, confirmed=False, chat_id=chat_id).order_by(
        '-timestamp')

    # confirm a photo
    if last_photo:
        if command == "sp":
            last_photo.first().confirmed = True

            if len(args) > 1:
                last_photo.first().caption = " ".join(args[1:])

            last_photo.first().save()

            bot.sendMessage(chat_id=chat_id, text="🌄 Your most recent photo was saved successfully.")
            # bot.sendPhoto(chat_id=chat_id, photo=last_photo.first().photo_id)

        # delete ALL unconfirmed photos
        last_photo.delete()
        return

    if command == "sp":
        bot.sendMessage(chat_id=chat_id, text="⚠️️ You didn't send a photo!")
        return

    # add command - add a user
    if command == "add" and len(args) > 1:
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
            bot.sendMessage(chat_id=chat_id,
                            text="%s was successfully deleted from the global chat group." % member_str)
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
            bot.sendMessage(chat_id=chat_id,
                            text="Quotes %s." % ("enabled" if quote_chat.quotes_enabled else "disabled"))
        else:
            bot.sendMessage(chat_id=chat_id, text="Usage: /quotes [enable/disable]")

    elif command == "sendquote" or command == "sq":

        print(update)

        # if it's a reply, then use the original message as the quote
        if 'reply_to_message' in update['message']:
            original_message = update['message']['reply_to_message']

            location = ""

            # if there's context (passed as the single argument) then add it
            if len(args) > 1:
                context = " ".join(args[1:])
            else:
                context = ""

            # this only really works if a message has an author and text
            if 'from' in original_message:
                author = original_message['from']['first_name']
                if 'last_name' in original_message['from']:
                    author += " " + original_message['from']['last_name']
            else:
                return

            if 'text' in original_message:
                quote = original_message['text']
            else:
                return

        # otherwise, try and parse the quote
        else:
            not_command = " ".join(args[1:])
            split = not_command.split("&&")

            try:
                quote = split[0].strip()
                author = split[1].strip()
            except IndexError:
                bot.sendMessage(chat_id=chat_id, text='⚠️ Usage: /sendquote quote && author [&& context] [&& location]')
                return

            try:
                context = split[2].strip()
            except IndexError:
                context = ""

            try:
                location = split[3].strip()
            except IndexError:
                location = ""

        new_quote = QuoteStorage(chat_id=chat_id, text=quote, author=author, context=context,
                                 location=location, sender=sender_username)
        new_quote.save()
        bot.sendMessage(chat_id=chat_id, text="👍 Quote saved successfully.")

    elif command == "getquote" or command == "gq":
        random_idx = random.randrange(0, QuoteStorage.objects.filter(chat_id=chat_id).count())
        random_obj = QuoteStorage.objects.filter(chat_id=chat_id)[random_idx]

        quote = generate_quote(random_obj)

        bot.sendMessage(chat_id=chat_id, text=quote, parse_mode="HTML")

    elif command == "getphoto" or command == "gp":
        count = Photo.objects.filter(chat_id=chat_id, confirmed=True).count()
        if count == 0:
            bot.sendMessage(chat_id=chat_id, text="😞 You don't have any photos yet! Try sending a photo and saving it "
                                                  "with /sp")
            return

        random_idx = random.randrange(0, count)
        random_obj = Photo.objects.filter(chat_id=chat_id, confirmed=True)[random_idx]
        bot.sendPhoto(chat_id=chat_id, photo=random_obj.photo_id, caption=random_obj.caption)

    elif command == "summon" or command == "braintrust" or command == "s":

        message_pieces = generate_summon(chat_id, update['message']['from']['username'],
                                         update['message']['from']['first_name'], " ".join(args[1:]))

        full_message = "%s\n\n%s" % (message_pieces[0], message_pieces[1])

        bot.sendMessage(chat_id=chat_id, text=full_message, parse_mode="HTML")

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
            random_idx = random.randrange(0, QuoteStorage.objects.filter(chat_id=chat_id).count())
            random_quote = QuoteStorage.objects.filter(chat_id=chat_id)[random_idx]

            meme_url = generate_meme(random_quote.text)
            bot.sendMessage(chat_id=chat_id, text=meme_url)

        # if there are no quotes, just give up
        except Exception as e:
            print(e)

    elif command == "8ball":
        random_idx = random.randrange(0, EightBallAnswer.objects.filter(chat_id=chat_id).count())
        random_answer = EightBallAnswer.objects.filter(chat_id=chat_id)[random_idx]
        bot.sendMessage(chat_id=chat_id, text="<i>%s</i>" % random_answer.answer, parse_mode="HTML")

    elif command == "quiplash":
        prompt = " ".join(args[1:]).strip()

        if prompt:
            db_prompt = QuiplashPrompt(prompt=prompt, sender_username=sender_username, chat_id=chat_id)
            db_prompt.save()
            bot.sendMessage(chat_id=chat_id, text="👍 Quiplash prompt saved successfully.")

        else:
            bot.sendMessage(chat_id=chat_id, text="⚠️ Usage: /quiplash [new prompt]")


    # otherwise it's not a real command :(
    else:
        bot.sendMessage(chat_id=chat_id, text="@%s: Command not found." % sender_username)


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

    random_meme = meme_ids[random.randrange(0, len(meme_ids))]

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
