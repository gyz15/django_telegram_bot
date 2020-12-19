import urllib
from os import environ
import json
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
        a = rawdata['message']['entities'][0]['type']
        return True
    except Exception as e:
        print(e)
    return False


def is_start(rawdata):
    try:
        start = rawdata['message']['text']
        return start == "/start"
    except:
        return False


def send_where_to_go(current_user):
    actions_list = []
    actions_can_be_done = current_user.current_location.action_can_be_taken.all()
    for action_obj in actions_can_be_done:
        actions_list.append([f'{action_obj.action_name}'])
    actions_list = json.dumps(actions_list)
    text = urllib.parse.quote_plus("Choose where do you want to go")
    url = URL + \
        f'sendMessage?chat_id={current_user.tg_id}&text={text}&reply_markup={{"keyboard":{actions_list},"one_time_keyboard":true,"force_reply":true}}'
    print(url)
    get_url(url)
