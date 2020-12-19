from django.shortcuts import render
from django.http import JsonResponse
import json
from .utils import send_message, is_start, send_where_to_go
from .models import TGUser

# Create your views here.


def main(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            # identify message type
            # todo handle user send msg and react to it sending inline keyboard or reply keyboard, and how to do conversation like system
            print(data)
            chat_id = data['message']['chat']['id']
            if is_start(data):
                first_name = data['message']['chat']['first_name']
                last_name = data['message']['chat']['last_name']
                try:
                    current_user = TGUser.objects.get(tg_id=chat_id)
                    if first_name != current_user.first_name or last_name != current_user.last_name:
                        current_user.first_name = first_name
                        current_user.last_name = last_name
                        current_user.save()
                    send_message(
                        f"Hey {current_user.first_name}, seems like u have chat with me before...", chat_id)
                except TGUser.DoesNotExist:
                    current_user = TGUser.objects.create(
                        tg_id=chat_id, first_name=first_name, last_name=last_name)
                    send_message(
                        f"Welcome {current_user.first_name}. I'm a bot. But currently i'm not available", chat_id)
                send_where_to_go(current_user)
            else:
                # todo handle user send de qiqiguaiguai things
                current_user = TGUser.objects.get(tg_id=chat_id)
                send_where_to_go(current_user)

            # todo handle user next conver
        except Exception as e:
            print(e)
            print("something went wrong")

    return JsonResponse({"ok": "POST request processed"})
