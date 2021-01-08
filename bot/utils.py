import urllib
from os import environ
import json
import requests
from decouple import config
from .models import TGUser, Action
from math import floor, log10

if config('ON_HEROKU', cast=int):
    BOT_TOKEN = config('DEPLOY_BOT_TOKEN')
else:
    BOT_TOKEN = config('TEST_BOT_TOKEN')
URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"


def send_message(text, chat_id):
    text = urllib.parse.quote_plus(text)
    url = URL + f"sendMessage?text={text}&chat_id={chat_id}"
    get_url(url)


def send_markdown_stock(text, chat_id):
    text = urllib.parse.quote_plus(text, safe="*")
    url = URL + \
        f"sendMessage?text={text}&chat_id={chat_id}&parse_mode=Markdown"
    get_url(url)
    # todo merge send_msg and send markdown together


def send_markdown_text(text, chat_id):
    url = URL + \
        f"sendMessage?text={text}&chat_id={chat_id}&parse_mode=Markdown"
    get_url(url)


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
    if current_user.current_location.name == "Page 3":
        subs_ark_fund(current_user)
    else:
        actions_list = []
        actions_can_be_done = current_user.current_location.action_can_be_taken.all()
        for action_obj in actions_can_be_done:
            actions_list.append([f'{action_obj.action_name}'])
        actions_list = json.dumps(actions_list)
        text = urllib.parse.quote_plus(
            f"You are currently at {current_user.current_location}. Choose where do you want to go")
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
            current_user.save()
            stop_action(current_user)
        elif action_obj.action_type == "AC":
            current_user.current_action = action_obj
            current_user.save()
            if action_obj.action_name == "Shout at Me":
                send_message(
                    "Okay, enter some word. Enter stop to end this section.", current_user.tg_id)
            elif action_obj.action_name == "Find Stock Data":
                send_message(
                    "Okay, enter a stock symbol.", current_user.tg_id)
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
    if len(symbol) <= 5 and symbol.isalpha():
        # sleep(10)
        raw_data = get_stock(symbol)
        if "errors" in raw_data.keys():
            send_message(
                f'The stock {symbol} could not be found', current_user.tg_id)
        else:
            if raw_data['data'][0]['attributes']['equityType'] != 'stocks':
                send_message(
                    f'{symbol} is not a stock', current_user.tg_id)
            else:
                # todo process data
                data = process_data(raw_data['data'][0]['attributes'])
                send_markdown_stock(f'{data}', current_user.tg_id)
    else:
        # fail to validate this is a symbol
        send_message(
            "This is not a valid symbol", current_user.tg_id)
    stop_action(current_user)


def get_stock(symbol):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'}
    data = requests.get(
        f"https://seekingalpha.com/api/v3/symbols/{symbol}/data", headers=headers)
    return data.json()


def process_data(stock_data):
    md_data = f'''
*Symbol*
{stock_data['name']}

*Name*
{stock_data['company']}

*Close*
{stock_data['close']}

*Description*
{stock_data['description']}

*Market Cap*
{millify(stock_data['marketCap'])}

*P/E Ratio (FWD)*
{to_2_d(stock_data['peRatioFwd'])}

*P/E Ratio (TTM)*
{to_2_d(stock_data['trailingPe'])}

*PEG Ratio (FWD)*
{to_2_d(stock_data['pegRatio'])}

*PS Ratio*
{to_2_d(stock_data['priceSales'])}

*PB Ratio*
{to_2_d(stock_data['priceBook'])}

*EPS*
{to_2_d(stock_data['eps'])}

*Estimate EPS*
{to_2_d(stock_data['estimateEps'])}

*Current Ratio*
{to_2_d(stock_data['curRatio'])}

*Debt / FCF*
{to_2_d(stock_data['debtFcf'])}

*Dividend Yield*
{to_2_d(stock_data['divYield'])}

*Revenue Growth (3Y)*
{change_percent(stock_data['revenueGrowth3'])}

*Earnings Growth (3Y)*
{change_percent(stock_data['earningsGrowth3'])}

*Free Cash Flow*
{millify(stock_data['fcf'])}

*ROE*
{change_percent(stock_data['roe'])}

*Gross Profit Margin(TTM)*
{change_percent(stock_data['grossMargin'])}

*Net Income*
{millify(stock_data['netIncome'])}
    '''
    return md_data


def millify(n):
    millnames = ['', 'K', 'M', 'B', 'T']
    n = float(n)
    millidx = max(0, min(len(millnames)-1,
                         int(floor(0 if n == 0 else log10(abs(n))/3))))

    return '{:.2f}{}'.format(n / 10**(3 * millidx), millnames[millidx])


def change_percent(string):
    if string != None and string != "NM":
        return f'{round(float(string), 2)}%'
    else:
        return None


def to_2_d(value):
    if value != "NM" and value != None:
        return round(float(value), 2)
    else:
        return None
