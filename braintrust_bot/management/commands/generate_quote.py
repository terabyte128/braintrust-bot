import random
import telegram
from django.core.management.base import BaseCommand
from braintrust_bot.models import QuoteChat, QuoteStorage
from braintrust_bot.views import generate_quote, generate_meme
from django_braintrust_bot.settings import API_KEY


class Command(BaseCommand):
    help = 'Sends a random quote to a random chat, so long as it is enabled'

    def handle(self, *args, **options):
        try:
            # initialize the bot for all views
            bot = telegram.Bot(token=API_KEY)

            chats = QuoteChat.objects.filter(quotes_enabled=True)

            for chat in chats:

                random_idx = random.randint(0, QuoteStorage.objects.filter(chat_id=chat.chat_id).count() - 1)
                random_quote = QuoteStorage.objects.filter(chat_id=chat.chat_id)[random_idx]

                # 50/50 chance every day
                if random.randint(0, 1) == 1:
                    quote = generate_quote(random_quote)
                    bot.sendMessage(chat_id=chat.chat_id, text=quote, parse_mode="HTML")
                else:
                    meme_url = generate_meme(random_quote.text)
                    bot.sendMessage(chat=chat.chat_id, text=meme_url)

        except Exception as e:
            print("Something went wrong with sending quote: " + str(e))
