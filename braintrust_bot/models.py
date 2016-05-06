from django.db import models

# Create your models here.


class ChatMember(models.Model):
    username = models.TextField(max_length=100, null=False, blank=False, unique=True)
