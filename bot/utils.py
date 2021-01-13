import urllib
from os import environ
import json
import requests
from decouple import config
from .models import TGUser, Action
from math import floor, log10
from fake_useragent import UserAgent
import re

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
            if action_obj.action_name == "Stock Analysis":
                send_message(
                    "Enter url.", current_user.tg_id
                )
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
                if current_action.action_name == "Find Stock Data":
                    find_stocks(words.upper(), current_user)
                elif current_action.action_name == "Stock Analysis":
                    if re.findall('https://seekingalpha.com/article/[0-9]+', words):
                        url = re.findall("article/[0-9]+-", words)[0]
                        key = url[8:-1]
                        find_news(words, key, current_user.tg_id)
                    else:
                        send_message("Invalid URL.", current_user.tg_id)
                else:
                    send_message(
                        "Sorry, this function is not done yet. Stay Tuned.", current_user.tg_id)
                    stop_action(current_user)
    else:
        # unproper message handling
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
    ua = UserAgent()
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'cookie': 'machine_cookie=3977770892613',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
    }
    data = requests.get(
        f"https://seekingalpha.com/api/v3/symbols/{symbol}/data", headers=headers)
    print(data.text)
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
    if n != None and n != "NM":
        millnames = ['', 'K', 'M', 'B', 'T']
        n = float(n)
        millidx = max(0, min(len(millnames)-1,
                             int(floor(0 if n == 0 else log10(abs(n))/3))))

        return '{:.2f}{}'.format(n / 10**(3 * millidx), millnames[millidx])
    return n


def change_percent(string):
    if string != None and string != "NM":
        return f'{round(float(string), 2)}%'
    else:
        return string


def to_2_d(value):
    if value != "NM" and value != None:
        return round(float(value), 2)
    else:
        return value


def find_news(original_url, key, chat_id):
    data = get_news_url(original_url, key)
    content = data['data']['attributes']['content']
    # Pre-handling
    content = content.replace("\n", "")
    content = re.sub(r'\*', "\\*", content)
    content = re.sub('`', "\`", content)
    content = re.sub('</div>\s?', "", content)

    # Handling p tag - making a new paragraph
    content = re.sub('</p>\s?', "\n\n", content)
    content = re.sub('<p>\s?', "", content)

    # Deleting div and span
    content = re.sub('<div["?@\s=a-zA-z0-9:/_.-]*>\s?', "", content)
    content = re.sub('<span["?@\s=a-zA-z0-9:/_.-]*>', "", content)
    content = re.sub('</span>', "", content)

    # Substitute double/triple bolded element with one * only
    content = re.sub(
        '<(h[1-6]|strong|b)["?@\s=a-zA-z0-9:/_.-]*><(h[1-6]|strong|b)["?@\s=a-zA-z0-9:/_.-]*>(<(h[1-6]|strong|b)["?@\s=a-zA-z0-9:/_.-]*>)?', '*', content)
    content = re.sub(
        '</(h[1-6]|strong|b)["?@\s=a-zA-z0-9:/_.-]*></(h[1-6]|strong|b)["?@\s=a-zA-z0-9:/_.-]*>(</(h[1-6]|strong|b)["?@\s=a-zA-z0-9:/_.-]*>)?', '*\n', content)

    # Ignore table
    content = re.sub('<table[<>"\n?@\s=a-zA-z0-9:/_.-]*>[-><"\n?@\s=a-zA-z0-9:/_./,/(/)]*</table>\s?',
                     '*-- Table Here. Stay Tuned --*\n\n', content)

    # Substitute left bolded element with one *
    content = re.sub('<h[1-6]["?@\s=a-zA-z0-9:/_.-]*>\s?', '*', content)
    content = re.sub('</h[1-6]["?@\s=a-zA-z0-9:/_.-]*>\s?', '*\n', content)
    content = re.sub('<strong["?@\s=a-zA-z0-9:/_.-]*>\s?', '*', content)
    content = re.sub('</strong>\s?', '*\n', content)
    content = re.sub('<b ["?@\s=a-zA-z0-9:/_.-]*>\s?', '*', content)
    content = re.sub('</b>\s?', '*\n', content)
    content = re.sub('</blockquote>\s?', '~~~~~~~~~~\n\n', content)
    content = re.sub(
        '<blockquote ["?@\s=a-zA-z0-9:/_.-]*>\s?', '~~~~~~~~~~\n', content)

    # Removing em tag
    content = re.sub('<em["?@\s=a-zA-z0-9:/_.-]*>\s?', '', content)
    content = re.sub('</em>\s?', '', content)

    # Making ordered or unordered list
    content = re.sub('<(u|o)l>\s?', '~~~~~~~~~~\n', content)
    content = re.sub('</(u|o)l>\s?', '~~~~~~~~~~\n\n', content)
    content = re.sub('<li>\s?', '>>', content)
    content = re.sub('</li>\s?', '\n\n', content)

    # Making figure
    content = re.sub('</figure["?@\s=a-zA-z0-9:/_.-]*>\s?',
                     "\n-\n\n", content)
    content = re.sub('<figure["?@\s=a-zA-z0-9:/_.-]*>\s?', "-\n", content)

    # Break line
    content = re.sub('<hr>', "------------\n\n", content)

    # Translate a tag in HTML to Markdown format
    a_tag_end = '</a>'
    link_href = '<a href="[\(\)+%~,?@#;&\s=a-zA-Z0-9:/_.-]*"'
    a_tag = '<a href="[\(\)+%~,?@#;&"\s=a-zA-Z0-9:/_.-]*>'
    href_with_tag = re.findall(link_href, content)
    total_a_tag = re.findall(a_tag, content)
    total_a_tag_end = re.findall(a_tag_end, content)

    for i in range(len(href_with_tag)):
        pure_link = href_with_tag[i][9:-1]
        start_tag = total_a_tag[i]
        end_tag = total_a_tag_end[i]
        content = content.replace(end_tag, f']({pure_link})', 1)
        content = content.replace(start_tag, "[", 1)

    # Replacing image with words and send it after whole message is sent
    img_src = '<img src="[?@=a-zA-z0-9:/_.-]*"'
    total_img_src = re.findall(img_src, content)
    total_img_src = [x[10:-1]for x in total_img_src]

    img_tag = '<img src="["#&,?@;\s=a-zA-Z0-9:/_.-]*>\s?'
    total_img_tag = re.findall(img_tag, content)
    for i in range(len(total_img_tag)):
        tag = total_img_tag[i]
        content = content.replace(tag, f"_Image {i+1}_")
    img_with_link_italic = re.findall("\[_Image [\d]+_]", content)

    # If image tag is wrapped by link, will remove the italic effect
    for word in img_with_link_italic:
        content = content.replace(word, re.sub("_", '', word))

    # Changing the words into url encode
    content = re.sub('&amp;', '%26', content)
    content = re.sub('#', '%23', content)

    # Splitting the content into small chunks to prevent too big messages and cause fail send
    content_chunk_list = small_chunk(content)
    for chunk in content_chunk_list:
        r = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={chat_id}&text={chunk}&parse_mode=markdown&disable_web_page_preview=True").json()
        # Pring error if got an error
        if r['ok'] == False:
            print("--------------------------------------------------------")
            print(r['description'])
            print(chunk)

    # Sending an image if there is one
    if len(total_img_src) != 0:
        for x in total_img_src:
            img = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto?chat_id={chat_id}&photo={x}&caption=Image {total_img_src.index(x)+1}")
            print(img.text)


def small_chunk(message):
    # Split the message into small chunks with size 3000 characters
    message_list = []
    formatted_message = []
    size = 3000
    chunk = ''
    split_text = message.split('\n')
    for t in split_text:
        if len(chunk) < size:
            chunk += f'{t}\n'
        else:
            message_list.append(chunk)
            chunk = ''
            chunk += f'{t}\n'
    message_list.append(chunk)
    return message_list


def get_news_url(original_url, key):
    # Get url by using requests and custom headers
    url = f'https://seekingalpha.com/api/v3/articles/{key}?include=author%2Cauthor.authorResearch%2Cco_authors%2CprimaryTickers%2CsecondaryTickers%2CotherTags%2Cpresentations%2Cpresentations.slides%2Csentiments%2CpromotedService'
    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip,deflate,br',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'cookie': 'machine_cookie=5356356749135',
        'pragma': 'no-cache',
        'referer': f'{original_url}',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
    }
    data = requests.get(url, headers=headers).json()
    return data
