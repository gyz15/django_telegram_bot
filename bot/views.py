from django.shortcuts import render
from django.http import JsonResponse
import json
from .utils import send_message, send_where_to_go, get_user_or_create, message_is_text, get_text, carry_out_action, carrying_action, handle_ark_add_rmv, is_valid_action_request, get_url
from .models import TGUser, Action
from decouple import config
from .ark import find_ark
# Create your views here.


def main(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            # identify message type
            print(data)
            current_user = get_user_or_create(data)
            user_id = current_user.tg_id
            # todo handle user send de qiqiguaiguai things
            # todo get user got current_action
            # if yes, try accepting other than text message
            # no, return false message
            # if no current_action
            # return error msg for all non text message
            # if is text, check if text is in the command that the user can use in this location
            # if can , carry out the command
            # if no, return user error message
            if current_user.current_action is not None:
                # todo handle message if user has current_action
                # todo is message a end word?
                # if not, continue action
                carrying_action(
                    current_user, current_user.current_action, data)
            else:
                if message_is_text(data):
                    if current_user.current_location.name == "Page 3" and get_text(data) != "Back To Home Page":
                        # similar carry out funcion here but for specifically ark only
                        text = get_text(data)
                        handle_ark_add_rmv(text, current_user)
                    else:
                        action = current_user.current_location.action_can_be_taken.filter(
                            action_name=get_text(data))
                        if len(action) == 1:
                            action = action[0]
                            carry_out_action(current_user, action)
                        else:
                            send_message("Sorry I can't get it", user_id)
                            send_where_to_go(current_user)
                else:
                    send_message("Sorry I'm unable to handle this", user_id)
                    send_where_to_go(current_user)

            # todo handle user next conver
        except Exception as e:
            print(e)
            print("something went wrong")

    return JsonResponse({'ok': "Request processed"})


def ark(request):
    if is_valid_action_request(request):
        find_ark()
        return JsonResponse({'ok': "Request processed"})
    else:
        return JsonResponse({'error': "Key not valid"})


def set_webhook(request):
    if is_valid_action_request(request):
        url = f"https://api.telegram.org/bot{config('DEPLOY_BOT_TOKEN')}/setWebhook?url={config('DOMAIN_NAME')}&drop_pending_updates=True"
        get_url(url)
        return JsonResponse({'ok': 'Webhook was set'})
    else:
        return JsonResponse({'error': "Webhook error"})


def delete_webhook(request):
    if is_valid_action_request(request):
        url = f"https://api.telegram.org/bot{config('DEPLOY_BOT_TOKEN')}/deleteWebhook"
        get_url(url)
        return JsonResponse({'ok': 'Webhook deleted'})
    else:
        return JsonResponse({'error': "An error occured"})
