from django.db import models

# Create your models here.


class ChatMember(models.Model):
    username = models.TextField(max_length=100, null=False, blank=False)
    chat_id = models.IntegerField(null=False, blank=False)

    class Meta:
        unique_together = ('username', 'chat_id')
