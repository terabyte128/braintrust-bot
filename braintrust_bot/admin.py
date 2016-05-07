from django.contrib import admin

# Register your models here.
from braintrust_bot.models import ChatMember, QuoteStorage, QuoteChat

admin.site.register(ChatMember)
admin.site.register(QuoteStorage)
admin.site.register(QuoteChat)