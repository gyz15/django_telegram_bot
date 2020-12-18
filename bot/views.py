from django.shortcuts import render
from django.http import JsonResponse
import json


# Create your views here.
def main(request):
    data = json.loads(request.body)
    # todo utils send the shit back
    return JsonResponse({"ok": "POST request processed"})
