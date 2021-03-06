from django.contrib import admin

# Register your models here.
from braintrust_bot.models import ChatMember, QuoteStorage, QuoteChat, ChatGroup, ChatGroupMember, Photo, \
    EightBallAnswer, QuiplashPrompt, Alexa

admin.site.register(ChatMember)
admin.site.register(QuoteStorage)
admin.site.register(QuoteChat)
admin.site.register(ChatGroup)
admin.site.register(ChatGroupMember)
admin.site.register(Photo)
admin.site.register(EightBallAnswer)
admin.site.register(QuiplashPrompt)
admin.site.register(Alexa)