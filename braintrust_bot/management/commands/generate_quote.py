import random
import telegram
from django.core.management.base import BaseCommand
from braintrust_bot.models import QuoteChat, QuoteStorage
from braintrust_bot.views import generate_quote
from django_braintrust_bot.settings import API_KEY


class Command(BaseCommand):
    help = 'Sends a random quote to a random chat, so long as it is enabled'

    def handle(self, *args, **options):
        try:
            random_idx = random.randint(0, QuoteStorage.objects.all().count() - 1)
            random_obj = QuoteStorage.objects.all()[random_idx]

            quote = generate_quote(random_obj)

            # initialize the bot for all views
            bot = telegram.Bot(token=API_KEY)

            chat = QuoteChat.objects.get(chat_id=random_obj.chat_id)

            if chat.quotes_enabled:
                bot.sendMessage(chat_id=random_obj.chat_id, text=quote, parse_mode="HTML")
        except Exception:
            pass