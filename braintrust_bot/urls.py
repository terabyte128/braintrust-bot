from django.conf.urls import url
from . import views
__author__ = 'Sam'


urlpatterns = [

    # webhook URL doesn't really need to be set unless we're actually changing the hook
    # (security concern otherwise)
    # url(r'^set_webhook', views.set_webhook, name="set_webhook"),

    # index page to verify that bot works
    url(r'^$', views.index, name="index"),

    # for retrieving webhook requests
    url(r'^webhook', views.webhook, name="webbook"),

    url(r'^sign_out', views.sign_out, name="sign_out"),

    url(r'^alexa', views.get_quote_alexa, name='get_quote_alexa')
]
