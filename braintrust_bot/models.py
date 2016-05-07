from django.db import models

# Create your models here.


class ChatMember(models.Model):
    username = models.TextField(max_length=100, null=False, blank=False)
    chat_id = models.IntegerField(null=False, blank=False)

    class Meta:
        unique_together = ('username', 'chat_id')

    def __str__(self):
        return self.username + "@" + str(self.chat_id)


class QuoteStorage(models.Model):
    chat_id = models.IntegerField(null=False, blank=False)
    text = models.TextField(max_length=500, null=False, blank=False)
    context = models.TextField(max_length=500, blank=True)
    author = models.TextField(max_length=100, null=False, blank=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.author) + "@" + str(self.chat_id) + " on " + str(self.timestamp)


class QuoteChat(models.Model):
    chat_id = models.IntegerField(null=False, blank=False, unique=True)
    quotes_enabled = models.BooleanField(default=False)

    def __str__(self):
        return str(self.chat_id) + ", " + str(self.quotes_enabled)