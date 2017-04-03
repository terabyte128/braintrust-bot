from django.contrib import admin

# Register your models here.
from braintrust_bot.models import ChatMember, QuoteStorage, QuoteChat, ChatGroup, ChatGroupMember

admin.site.register(ChatMember)
admin.site.register(QuoteStorage)
admin.site.register(QuoteChat)
admin.site.register(ChatGroup)
admin.site.register(ChatGroupMember)
