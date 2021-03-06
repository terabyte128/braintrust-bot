from django.db import models

# Create your models here.


class ChatMember(models.Model):
    username = models.TextField(max_length=100, null=False, blank=False)
    chat_id = models.BigIntegerField(null=False, blank=False)

    class Meta:
        unique_together = ('username', 'chat_id')

    def __str__(self):
        return self.username + "@" + str(self.chat_id)


class QuoteStorage(models.Model):
    chat_id = models.BigIntegerField(null=False, blank=False)
    text = models.TextField(max_length=500, null=False, blank=False)
    context = models.TextField(max_length=500, blank=True)
    author = models.TextField(max_length=100, null=False, blank=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.TextField(max_length=500, blank=True, null=True)
    sender = models.TextField(max_length=100, null=True, blank=True)

    def __str__(self):
        return str(self.author) + "@" + str(self.chat_id) + " on " + str(self.timestamp)


class Photo(models.Model):
    chat_id = models.BigIntegerField(null=False, blank=False)
    caption = models.TextField(null=True, blank=True)
    sender = models.TextField(max_length=100, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    photo_id = models.TextField()
    confirmed = models.BooleanField(default=False)
    sender_username = models.TextField(null=True, blank=True)

    def __str__(self):
        return "confirmed = " + str(self.confirmed) + "  " + str(self.caption) + " by " + str(self.sender) + " @ " + str(self.chat_id)


class QuoteChat(models.Model):
    name = models.TextField(null=True, blank=True)
    chat_id = models.BigIntegerField(null=False, blank=False, unique=True)
    quotes_enabled = models.BooleanField(default=False)

    def __str__(self):
        return str(self.chat_id) + ", " + str(self.quotes_enabled)


class ChatGroup(models.Model):
    name = models.TextField(max_length=100, null=False, blank=False)
    chat_id = models.BigIntegerField(null=False, blank=False)

    class Meta:
        unique_together = ('name', 'chat_id')


class ChatGroupMember(models.Model):
    username = models.TextField(max_length=100, null=False, blank=False)
    chat_group = models.ForeignKey(ChatGroup)

    class Meta:
        unique_together = ('username', 'chat_group')


class EightBallAnswer(models.Model):
    answer = models.TextField(null=False, blank=False)
    chat_id = models.BigIntegerField(null=False, blank=False)

    def __str__(self):
        return self.answer + " @ " + str(self.chat_id)


class QuiplashPrompt(models.Model):
    prompt = models.TextField()
    sender_username = models.TextField(max_length=100, null=True, blank=True)
    chat_id = models.BigIntegerField(null=False, blank=False)


class Alexa(models.Model):
    device_user_id = models.TextField(max_length=255, null=False, blank=False)
    chat = models.ForeignKey(QuoteChat, blank=True, null=True)  # chat to which this alexa is associated
