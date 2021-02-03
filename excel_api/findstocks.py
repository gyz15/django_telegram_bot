# TODO a function that can fetch data and process it into json object
import requests


def is_valid_stock(stock):
    '''Check user submission validity'''
    if len(stock) <= 5 and stock.isalpha() adn len(stock) > 0:
        return True
    return False


def find_stock(stock):
    '''Main function '''
    return_res = {}
    if not is_valid_stock(stock):
        return {"Error": "Object is not a valid stock symbol"}
    fetch_from_sa()
    # fetch from sa
    # if sa data no prob
    # try clean
    # real time price
    # no prob clean
    # combine data
    # calc call_left
    # return response
    user_obj.call_used_today += 1
    user_obj.save(update_fields=['call_used_today'])
    call_left = user_obj.plan.api_per_day - user_obj.call_used_today


def fetch_from_sa(url):
    '''Fetch data from SA'''
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
    }
    data = requests.get(url, headers=headers).json()
    if "errors" in data:
        return {"Errors": data['errors'][0]['detail']}
    return data


def clean_data(data):
