from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('', csrf_exempt(views.main), name="main"),
    path('setwebhook/', csrf_exempt(views.set_webhook), name="setwebhook"),
    path('deletewebhook/', csrf_exempt(views.delete_webhook), name="deletewebhook"),
]
