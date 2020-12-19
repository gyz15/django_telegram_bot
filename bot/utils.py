import urllib
from os import environ
import requests
from decouple import config

TOKEN = config('TOKEN')
URL = f"https://api.telegram.org/bot{TOKEN}/"


def send_message(text, chat_id):
    text = urllib.parse.quote_plus(text)
    url = URL + f"sendMessage?text={text}&chat_id={chat_id}"
    get_url(url)


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def is_command(rawdata):
    try:
        print(rawdata['message']['entities'][0]['type'])
        return True
    except Exception as e:
        print(e)
    return False
