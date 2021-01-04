import urllib
from os import environ
import json
import requests
from decouple import config
from .models import TGUser, Action, ArkFund
# from time import sleep
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
                if current_user.alphavantage_api_key is not None:
                    send_message(
                        "Okay, enter a stock symbol.", current_user.tg_id)
                else:
                    action_to_be_carry = Action.objects.get(
                        action_name="Setup API Key")
                    carry_out_action(current_user, action_to_be_carry)
            elif action_obj.action_name == "Setup API Key":
                text = '''
1. Go to [Alpha Vantage](https://www.alphavantage.co/support/#api-key) and claim your API key.\n
2. Enter the details and click "GET FREE API KEY".\n
3. Copy the key and paste it here to send me.\n
                '''
                text = urllib.parse.quote_plus(text)
                send_markdown_text(text, current_user.tg_id)
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
                    if api_is_valid(words):
                        current_user.alphavantage_api_key = words
                        current_user.save()
                        send_message("Ok API Key Set.", current_user.tg_id)
                        stop_action(current_user)
                    else:
                        send_message(
                            "API Key is not set. (Format Error)", current_user.tg_id)
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
        raw_data = get_stock(
            symbol, current_user.alphavantage_api_key, "OVERVIEW")
        cash_flow_data = get_stock(
            symbol, current_user.alphavantage_api_key, "CASH_FLOW")
        if raw_data == {}:
            # raw_data
            # todo validate data is blank(user didn't give a good symbol)
            # todo send the message in html or md ??format
            # todo send a wait message ..... and remove it when finding
            send_message(
                f"Hmmm, look like {symbol} is not a valid symbol, or I can't find it... ", current_user.tg_id)
        elif "Note" in raw_data.keys() or "Note" in cash_flow_data.keys():
            send_message(
                'Due to the limitations, you can only look for 2 symbols per minute and 250 symbols per day. Please try again later.', current_user.tg_id)
        else:
            # No problem in both data from alphavantage
            # todo process data
            overview_data = process_data(raw_data)
            final_md = process_cash_flow(overview_data, cash_flow_data)
            send_markdown_stock(f'{final_md}', current_user.tg_id)
    else:
        # fail to validate this is a symbol
        send_message(
            "This is not a valid symbol", current_user.tg_id)
    stop_action(current_user)


def get_stock(symbol, api_key, find_type):
    data = requests.get(
        f"https://www.alphavantage.co/query?function={find_type}&symbol={symbol}&apikey={api_key}")
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
{change_percent(stock_data['DividendYield'])}

*EPS*
{stock_data['EPS']}

*Profit Margin*
{change_percent(stock_data['ProfitMargin'])}

*Operating Margin*
{change_percent(stock_data['OperatingMarginTTM'])}

*ROE*
{change_percent(stock_data['ReturnOnEquityTTM'])}

*Quarterly Earnings Growth (YOY)*
{change_percent(stock_data['QuarterlyEarningsGrowthYOY'])}

*Quarterly Revenue Growth (YOY)*
{change_percent(stock_data['QuarterlyRevenueGrowthYOY'])}

*Beta*
{change_beta(stock_data['Beta'])}

*Short Percent Float*
{"{:.2%}".format(float(stock_data['ShortPercentFloat']))}
    '''
    # for key, value in stock_data.items():
    #     md_data += f'{key}\n{value}\n\n'
    # print(md_data)
    return md_data


def process_cash_flow(md_data, stock_data):
    # md_data -> to send user
    # stock_data -> raw data from alphavantage
    cf_message = ""
    num_of_year = 0
    net_income = []
    fiscal_date_ending = []
    free_cash_flow = []
    try:
        for i in range(5):
            fiscal_date_ending = stock_data['annualReports'][i]['fiscalDateEnding']
            num_of_year += 1
            net_income = millify(
                int(stock_data['annualReports'][i]['netIncome']))
            free_cash_flow = millify(int(stock_data['annualReports'][i]['operatingCashflow'])-int(
                stock_data['annualReports'][i]['capitalExpenditures']))
            cf_message += f'''
Fiscal Date Ending : {fiscal_date_ending}
Net Income : {net_income}
Free Cash Flow (CFOA-CapEx) : {free_cash_flow}
'''
    except IndexError:
        pass
    md_data += f"\n*Annual Reports (Previous {num_of_year} years)*"
    md_data += cf_message
    return md_data


def api_is_valid(api_key):
    return api_key.isalnum() and len(api_key) == 16


def millify(n):
    millnames = ['', 'K', 'M', 'B', 'T']
    n = float(n)
    millidx = max(0, min(len(millnames)-1,
                         int(floor(0 if n == 0 else log10(abs(n))/3))))

    return '{:.2f}{}'.format(n / 10**(3 * millidx), millnames[millidx])


def change_percent(string):
    if string != "None":
        return "{:.2%}".format(float(string))
    else:
        return None


def change_beta(beta):
    if beta != "None":
        return round(float(beta), 2)
    else:
        return "-"


def subs_ark_fund(current_user):
    text = 'You have subscribed on these ARK ETFs:'
    action_list = []
    for fund in ArkFund.objects.all():
        if current_user in fund.subscriber.all():
            text += f'\n✅ {fund.ticker}'
            action_list.append([urllib.parse.quote_plus(
                f'⛔ Unubscibe for {fund.ticker}')])
        else:
            text += f'\n⛔ {fund.ticker}'
            action_list.append([urllib.parse.quote_plus(
                f'✅ Subscibe for {fund.ticker}')])
    action_list.append(['Back To Home Page'])
    text = urllib.parse.quote_plus(text)
    action_list = json.dumps(action_list)
    url = URL + \
        f'sendMessage?chat_id={current_user.tg_id}&text={text}&reply_markup={{"keyboard":{action_list},"one_time_keyboard":true,"force_reply":true}}'
    get_url(url)
    # todo set action for set ark
    # todo handle add delete ark status


def handle_ark_add_rmv(text, current_user):
    add = True
    ark_list = ['ARKK', 'ARKQ', 'ARKW', 'ARKF', 'ARKG']
    try:
        if ("⛔ Unubscibe for ARK" in text or "✅ Subscibe for ARK" in text) and text[-4:] in ark_list:
            add = "✅ Subscibe for ARK" in text
            fund = ArkFund.objects.get(ticker=text[-4:])
            if add:
                if current_user not in fund.subscriber.all():
                    fund.subscriber.add(current_user)
                    send_message(
                        f"You have subscribed from {fund.ticker}", current_user.tg_id)
                else:
                    send_message(
                        f"You have already subscribed for {fund.ticker}", current_user.tg_id)
            else:
                if current_user in fund.subscriber.all():
                    fund.subscriber.remove(current_user)
                    send_message(
                        f"You have unsubscribed from {fund.ticker}", current_user.tg_id)
                else:
                    send_message(
                        f"You have already unsubscribed from {fund.ticker}", current_user.tg_id)
            fund.save()
        else:
            send_message(
                "Format error for message, Sorry I can't get it", current_user.tg_id)
    except Exception as e:
        print(e)
        send_message("Some Error occured.....", current_user.tg_id)
    send_where_to_go(current_user)


def is_valid_action_request(request):
    try:
        data = json.loads(request.body)
        return request.method == "POST" and data['key'] == config('ACTION_KEY')
    except Exception as e:
        print(e)
