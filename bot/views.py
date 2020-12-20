from django.shortcuts import render
from django.http import JsonResponse
import json
from .utils import send_message, send_where_to_go, get_user_or_create, message_is_text, get_text
from .models import TGUser, Action

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
                pass
            else:
                # todo check message is text or not
                if message_is_text(data):
                    # is user sending a valid text command?
                    action = current_user.current_location.action_can_be_taken.filter(
                        action_name=get_text(data))
                    if len(action) == 1:
                        pass
                    else:
                        send_message("sorry i can't get it", user_id)

            send_where_to_go(current_user)

            # todo handle user next conver
        except Exception as e:
            print(e)
            print("something went wrong")

    return JsonResponse({"ok": "Request processed"})
