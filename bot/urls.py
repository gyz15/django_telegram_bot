from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('', csrf_exempt(views.main), name="main"),
    path('ark/', csrf_exempt(views.ark), name="ark"),
]
