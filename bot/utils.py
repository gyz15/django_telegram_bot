import urllib
from os import environ
import json
import requests
from decouple import config
from .models import TGUser, Action

TOKEN = config('TOKEN')
API_KEY = config('ALPHAVANTAGE_API_KEY')
URL = f"https://api.telegram.org/bot{TOKEN}/"


def send_message(text, chat_id):
    text = urllib.parse.quote_plus(text)
    url = URL + f"sendMessage?text={text}&chat_id={chat_id}"
    get_url(url)


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_text(rawdata):
    try:
        return rawdata['message']['text']
    except Exception as e:
        print(e)
        return ''


def send_where_to_go(current_user):
    actions_list = []
    actions_can_be_done = current_user.current_location.action_can_be_taken.all()
    for action_obj in actions_can_be_done:
        actions_list.append([f'{action_obj.action_name}'])
    actions_list = json.dumps(actions_list)
    text = urllib.parse.quote_plus("Choose where do you want to go")
    url = URL + \
        f'sendMessage?chat_id={current_user.tg_id}&text={text}&reply_markup={{"keyboard":{actions_list},"one_time_keyboard":true,"force_reply":true}}'
    get_url(url)


def message_is_text(rawdata):
    try:
        text = rawdata['message']
        keylist = list(text)
        return 'text' in keylist
    except:
        # might be callback_query
        return False


def get_user_or_create(rawdata):
    '''Do some checking on database, create user if necesarry'''
    try:
        first_name = rawdata['message']['chat']['first_name']
        last_name = rawdata['message']['chat']['last_name']
        chat_id = rawdata['message']['chat']['id']
        current_user = TGUser.objects.get(tg_id=chat_id)
        if first_name != current_user.first_name or last_name != current_user.last_name:
            current_user.first_name = first_name
            current_user.last_name = last_name
            current_user.save()
        return current_user
    except TGUser.DoesNotExist:
        current_user = TGUser.objects.create(
            tg_id=chat_id, first_name=first_name, last_name=last_name)
        current_user.save()
        send_message(
            f"Welcome {current_user.first_name}. I'm a bot. But currently i'm not available", chat_id)
        return current_user


def carry_out_action(current_user, action_obj):
    if action_obj.action_type == "GO":
        current_user.current_location = action_obj.go_to
        stop_action(current_user)
    elif action_obj.action_type == "AC":
        if action_obj.action_name == "Shout at Me":
            current_user.current_action = action_obj
            current_user.save()
            send_message(
                "Okay, enter some word. Enter stop to end this section.", current_user.tg_id)
        else:
            send_message(
                "Sorry, this function is not done yet. Stay Tuned.", current_user.tg_id)
            stop_action(current_user)
    else:
        print("Strange action by user")


def carrying_action(current_user, current_action, data):
    if message_is_text(data):
        # stop message needs to be text, if user not sending text sure not stopping the things
        if get_text(data).upper() == current_action.end_action_code.upper():
            stop_action(current_user)
        else:
            if current_action.action_name == "Shout at Me":
                words = get_text(data)
                try:
                    action_obj = current_user.current_location.action_can_be_taken.get(
                        action_name=words)
                    carry_out_action(current_user, action_obj)
                except Action.DoesNotExist:
                    send_message(f"{words.upper()}", current_user.tg_id)
    else:
        if current_action.action_name == "Shout at Me":
            send_message(
                "Looks like I can't shout you what you're saying", current_user.tg_id)
        else:
            send_message(
                "Sorry, this function is not done yet. Stay Tuned.", current_user.tg_id)
            stop_action(current_user)


def stop_action(current_user):
    current_user.current_action = None
    current_user.save()
    send_where_to_go(current_user)
