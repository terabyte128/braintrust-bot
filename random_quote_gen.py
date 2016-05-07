import os
import random
import telegram
from braintrust_bot.views import generate_quote
import django
from braintrust_bot.models import QuoteStorage, QuoteChat
from django_braintrust_bot.settings import API_KEY

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_braintrust_bot.settings")

django.setup()

random_idx = random.randint(0, QuoteStorage.objects.all().count() - 1)
random_obj = QuoteStorage.objects.all()[random_idx]

quote = generate_quote(random_obj)


# initialize the bot for all views
bot = telegram.Bot(token=API_KEY)

chat = QuoteChat.objects.get(chat_id=random_obj.chat_id)

if chat.quotes_enabled:
    bot.sendMessage(chat_id=random_obj.chat_id, text=quote, parse_mode="HTML")
