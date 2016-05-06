from django.conf.urls import url
from . import views
__author__ = 'Sam'


urlpatterns = [
    # url(r'^set_webhook', views.set_webhook, name="set_webhook"),
    url(r'^$', views.index, name="index"),
    url(r'^webhook', views.webhook, name="webbook"),
]
