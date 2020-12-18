from django.shortcuts import render
from django.http import JsonResponse
import json
from .utils import send_message

# Create your views here.


def main(request):
    data = json.loads(request.body)
    print(data)
    try:
        text = data["message"]["text"]
        chat_id = data["message"]["chat"]["id"]
        send_message(text, chat_id)
    except KeyError:
        print("Something I don't know")
    return JsonResponse({"ok": "POST request processed"})
