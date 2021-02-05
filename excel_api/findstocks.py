# TODO a function that can fetch data and process it into json object
import requests


def is_valid_stock(symbol):
    '''Check user submission validity'''
    if len(symbol) <= 5 and symbol.isalpha() and len(symbol) > 0:
        return True
    return False


def find_stock(symbol, user_obj):
    '''Main function '''
    return_res = {}
    if not is_valid_stock(symbol):
        return {"Error": "Object is not a valid symbol"}
    data1 = fetch_from_sa_data(symbol)
    data2 = fetch_from_sa_prices(symbol)
    return_res.update(data1)
    return_res.update(data2)
    user_obj.call_used_today += 1
    user_obj.save(update_fields=['call_used_today'])
    call_left = user_obj.plan.api_per_day - user_obj.call_used_today
    return {"user_data": {"call_left": call_left}, "stock_data": return_res}


def fetch_from_sa_data(symbol):
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
    raw_data = requests.get(
        f"https://seekingalpha.com/api/v3/symbols/{symbol}/data", headers=headers).json()
    if "errors" in raw_data:
        return {"Error": raw_data['errors'][0]['detail']}
    else:
        if raw_data['data'][0]['attributes']['equityType'] != 'stocks':
            return {"Error": "It is not a valid stock"}
        else:
            clean_data = clean_data_data(raw_data)
    return clean_data


def clean_data_data(raw_data):
    d = dict()
    name = raw_data['data'][0]['attributes']['name']
    company = raw_data['data'][0]['attributes']['company']
    longdesc = raw_data['data'][0]['attributes']['longDesc']
    revenuegrowth = raw_data['data'][0]['attributes']['revenueGrowth']
    revenuegrowth3 = raw_data['data'][0]['attributes']['revenueGrowth3']
    earningsgrowth = raw_data['data'][0]['attributes']['earningsGrowth']
    earningsgrowth3 = raw_data['data'][0]['attributes']['earningsGrowth3']
    divYield = raw_data['data'][0]['attributes']['divYield']
    divYield4y = raw_data['data'][0]['attributes']['divYield4y']
    dividendconsistency = raw_data['data'][0]['attributes']['dividendConsistency']
    dividendgrowth = raw_data['data'][0]['attributes']['dividendGrowth']
    payoutratio = raw_data['data'][0]['attributes']['payoutRatio']
    payout4y = raw_data['data'][0]['attributes']['payout4y']
    peratiofwd = raw_data['data'][0]['attributes']['peRatioFwd']
    trailingpe = raw_data['data'][0]['attributes']['trailingPe']
    pegratio = raw_data['data'][0]['attributes']['pegRatio']
    pricebook = raw_data['data'][0]['attributes']['priceBook']
    pricesales = raw_data['data'][0]['attributes']['priceSales']
    eps = raw_data['data'][0]['attributes']['eps']
    fcfshare = raw_data['data'][0]['attributes']['fcfShare']
    curratio = raw_data['data'][0]['attributes']['curRatio']
    quickratio = raw_data['data'][0]['attributes']['quickRatio']
    grossmargin = raw_data['data'][0]['attributes']['grossMargin']
    roe = raw_data['data'][0]['attributes']['roe']
    roa = raw_data['data'][0]['attributes']['roa']
    d = {
        "symbol": name,
        "company_name": company,
        "description": longdesc,
        "revenue_growth": revenuegrowth,
        "revenue_growth_3": revenuegrowth3,
        "earnings_growth": earningsgrowth,
        "earnings_growth_3": earningsgrowth3,
        "d_y": divYield,
        "d_y_4": divYield4y,
        "div_con": dividendconsistency,
        "div_growth": dividendgrowth,
        "payout_ratio": payoutratio,
        "payout_4": payout4y,
        "pe_fwd": peratiofwd,
        "pe_t": trailingpe,
        "peg_ratio": pegratio,
        "p_b_ratio": pricebook,
        "p_s_ratio": pricesales,
        "e_p_s": eps,
        "fcf_share": fcfshare,
        "cur_ratio": curratio,
        "quick_ratio": quickratio,
        "gross_margin": grossmargin,
        "roe": roe,
        "roa": roa,
    }
    for key, val in d.items():
        if val == None:
            d[key] = "-"
    print(type(d), d)
    return d


def clean_data_prices(raw_data):
    last = raw_data['data'][0]['attributes']['last']
    change = raw_data['data'][0]['attributes']['change']
    percent_change = raw_data['data'][0]['attributes']['percentChange']

    return {
        "last": last,
        "change": change,
        "percent_change": percent_change,
    }


def fetch_from_sa_prices(symbol):
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
    raw_data = requests.get(
        f"https://finance.api.seekingalpha.com/v2/real-time-prices?symbols={symbol}", headers=headers).json()
    if "errors" in raw_data:
        return {"Error": raw_data['errors'][0]['detail']}
    final_data = clean_data_prices(raw_data)
    return final_data
