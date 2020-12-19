from django.shortcuts import render
from django.http import JsonResponse
import json
from .utils import send_message, is_command

# Create your views here.


def main(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            # identify message type
            # todo handle user send msg and react to it sending inline keyboard or reply keyboard, and how to do conversation like system
            print(data)
            print(is_command(data))
            chat_id = data['message']['chat']['id']
            keylist = list(data['message'])
            typeof_msg = keylist[4]
            msg = data['message'][keylist[4]]
            if typeof_msg == 'text':
                send_message(
                    f'U are sending {typeof_msg}, the content is "{msg}"', chat_id)
            else:
                send_message(
                    f"U are sending {typeof_msg}, But I can't send you back", chat_id)
        except Exception as e:
            print("something went wrong")

    return JsonResponse({"ok": "POST request processed"})
