import urllib
from os import environ
import json
import requests
from decouple import config
from .models import TGUser, Action
# from time import sleep
from math import floor, log10

TOKEN = config('TOKEN')
URL = f"https://api.telegram.org/bot{TOKEN}/"


def send_message(text, chat_id):
    text = urllib.parse.quote_plus(text)
    url = URL + f"sendMessage?text={text}&chat_id={chat_id}"
    get_url(url)


def send_markdown(text, chat_id):
    # text = urllib.parse.quote_plus(text)
    url = URL + \
        f"sendMessage?text={text}&chat_id={chat_id}&parse_mode=Markdown"
    get_url(url)
    # todo merge send_msg and send markdown together


def get_url(url):
    response = requests.get(url)
    # print(response.json())
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
            f"Hello {current_user.first_name}", chat_id)
        return current_user


def carry_out_action(current_user, action_obj):
    if action_obj.is_developing and current_user.is_developer is not True:
        send_message(
            "Sorry, this function is currently in mantainance or developing. Stay Tuned.", current_user.tg_id)
        stop_action(current_user)
    else:
        if action_obj.action_type == "GO":
            current_user.current_location = action_obj.go_to
            stop_action(current_user)
        elif action_obj.action_type == "AC":
            current_user.current_action = action_obj
            current_user.save()
            if action_obj.action_name == "Shout at Me":
                send_message(
                    "Okay, enter some word. Enter stop to end this section.", current_user.tg_id)
            elif action_obj.action_name == "Find Stock Data":
                if current_user.alphavantage_api_key is not None:
                    send_message(
                        "Okay, enter a stock symbol.", current_user.tg_id)
                else:
                    action_to_be_carry = Action.objects.get(
                        action_name="Setup API Key")
                    carry_out_action(current_user, action_to_be_carry)
            elif action_obj.action_name == "Setup API Key":
                send_message("This is the steps to get an api key",
                             current_user.tg_id)
                # todo steps to setup api key sent to user
            else:
                send_message(
                    "Can't detect action name and perform action.", current_user.tg_id)
                stop_action(current_user)
        else:
            print("Strange action by user")


def carrying_action(current_user, current_action, data):
    if message_is_text(data):
        # stop message needs to be text, if user not sending text sure not stopping the things
        if get_text(data).upper() == current_action.end_action_code.upper():
            stop_action(current_user)
        else:
            # proper message handling
            words = get_text(data)
            try:
                action_obj = current_user.current_location.action_can_be_taken.get(
                    action_name=words)
                carry_out_action(current_user, action_obj)
            except Action.DoesNotExist:
                if current_action.action_name == "Shout at Me":
                    send_message(f"{words.upper()}", current_user.tg_id)
                elif current_action.action_name == "Find Stock Data":
                    find_stocks(words.upper(), current_user)
                elif current_action.action_name == "Setup API Key":
                    current_user.alphavantage_api_key = words
                    current_user.save()
                    send_message("Ok API Key Set.", current_user.tg_id)
                    stop_action(current_user)
                else:
                    send_message(
                        "Sorry, this function is not done yet. Stay Tuned.", current_user.tg_id)
                    stop_action(current_user)
    else:
        # unproper message handling
        # if current_action.action_name == "Shout at Me":
        send_message(
            "Error. Type of message is not suitable to carry out action.", current_user.tg_id)
        stop_action(current_user)


def stop_action(current_user):
    current_user.current_action = None
    current_user.save()
    send_where_to_go(current_user)


def find_stocks(symbol, current_user):
    # validation for symbol before checking to prevent wastage of api
    if len(symbol) <= 5 and symbol.isalpha():
        # sleep(10)
        raw_data = get_stock(symbol, current_user.alphavantage_api_key)
        if raw_data == {}:
            # raw_data
            # todo validate data is blank(user didn't give a good symbol)
            # todo send the message in html or md ??format
            # todo send a wait message ..... and remove it when finding
            send_message(
                f"Hmmm, look like {symbol} is not a valid symbol, or I can't find it... ", current_user.tg_id)
        elif "Note" in raw_data.keys():
            send_message(
                'U have reach the limit, please try again later', current_user.tg_id)
        else:
            # data look like no problem
            # todo process data
            processed_data = process_data(raw_data)
            send_markdown(f'{processed_data}', current_user.tg_id)
    else:
        # fail to validate this is a symbol
        send_message(
            "This is not a valid symbol", current_user.tg_id)
    stop_action(current_user)


def get_stock(symbol, api_key):
    data = requests.get(
        f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}")
    return data.json()


def process_data(stock_data):
    md_data = f'''
*Symbol*
{stock_data['Symbol']}

*Name*
{stock_data['Name']}

*Description*
{stock_data['Description']}

*Market Cap*
{millify(stock_data['MarketCapitalization'])}

*P/E Ratio*
{stock_data['PERatio']}

*PEG Ratio*
{stock_data['PEGRatio']}

*P/Sales Ratio*
{stock_data['PriceToSalesRatioTTM']}

*P/B Ratio*
{stock_data['PriceToBookRatio']}

*Dividend Yield*
{"{:.2%}".format(float(stock_data['DividendYield']))}

*EPS*
{stock_data['EPS']}

*Profit Margin*
{"{:.2%}".format(float(stock_data['ProfitMargin']))}

*Operating Margin*
{"{:.2%}".format(float(stock_data['OperatingMarginTTM']))}

*ROE*
{"{:.2%}".format(float(stock_data['ReturnOnEquityTTM']))}

*Quarterly Earnings Growth (YOY)*
{"{:.2%}".format(float(stock_data['QuarterlyEarningsGrowthYOY']))}

*Quarterly Revenue Growth (YOY)*
{"{:.2%}".format(float(stock_data['QuarterlyRevenueGrowthYOY']))}

*Beta*
{round(float(stock_data['Beta']),2)}

*Short Percent Float*
{"{:.2%}".format(float(stock_data['ShortPercentFloat']))}
    '''
    # for key, value in stock_data.items():
    #     md_data += f'{key}\n{value}\n\n'
    # print(md_data)
    return md_data


def millify(n):
    millnames = ['', 'K', 'M', 'B', 'T']
    n = float(n)
    millidx = max(0, min(len(millnames)-1,
                         int(floor(0 if n == 0 else log10(abs(n))/3))))

    return '{:.2f}{}'.format(n / 10**(3 * millidx), millnames[millidx])
