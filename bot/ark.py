from .models import ArkFund, ArkStock, TGUser
from .utils import send_message
import pandas as pd
import requests
import os
from .utils import send_markdown_stock, send_message
import time
from datetime import date, timedelta
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
import numpy as np


def find_ark():
    # try:
    for etf in ArkFund.objects.all():
        print(etf.ticker)
        with requests.get(etf.file_url, stream=True) as r:
            with open(f".\{etf.ticker}.csv", "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        new_data = pd.read_csv(
            f".\{etf.ticker}.csv", parse_dates=[0], dayfirst=True, skipfooter=3, engine='python')
        sending_data = {"added": [], "removed": [],
                        "buying": [], "selling": []}
        new_data.fillna("-", inplace=True)
        # Comparing latest data with the data in the database
        for company_name in new_data.company:
            new_company = new_data.loc[new_data.company == company_name]
            print(company_name)
            try:
                stock = etf.stocks.get(company=company_name)
                sending_data, stock = handle_stock_add_minus(
                    sending_data, new_company, stock)
                stock.had_changes = True
                stock.save()
            except ObjectDoesNotExist:
                # todo handle message here
                fund = new_company['fund'].values[0]
                company = new_company['company'].values[0]
                ticker = new_company['ticker'].values[0]
                shares = new_company['shares'].values[0]
                weight = new_company['weight(%)'].values[0]
                fund_obj = ArkFund.objects.get(ticker=fund)
                stock = ArkStock.objects.create(
                    company=company, ticker=ticker, shares=shares, weight=weight, fund=fund_obj)
                stock.save()
                data = []
                data.append(stock.company)
                data.append(stock.ticker)
                data.append(stock.shares)
                data.append(stock.weight)
                sending_data['added'].append(data)
        removed_stocks = etf.stocks.filter(had_changes=False)
        for stock in removed_stocks:
            data = []
            data.append(stock.company)
            data.append(stock.ticker)
            data.append(stock.shares)
            sending_data['removed'].append(data)
            stock.delete()
        if os.path.exists(f".\{etf.ticker}.csv"):
            os.remove(f".\{etf.ticker}.csv")
        else:
            pass
        todays_date = date.today() - timedelta(days=1)
        date_val = todays_date.strftime('%d/%m/%y')
        message = f'Changes of {etf.ticker} on {date_val}:'
        if sending_data['added'] != []:
            message += "\n*Stocks newly added into the fund:*"
            for data in sending_data['added']:
                message += f'''
{data[0]}({data[1]})
Shares bought: {data[2]}
Weight: {data[3]}%'''
        else:
            message += "\n*(No stocks were newly added)*"
        if sending_data['removed'] != []:
            message += "\n*Stocks removed from the fund:*"
            for data in sending_data['removed']:
                message += f'''
{data[0]}({data[1]})
Shares sold: {data[2]}'''
        else:
            message += "\n*(No stocks were removed)*"
        if sending_data['buying'] != []:
            message += "\n*Stocks were bought by the fund:*"
            for data in sending_data['buying']:
                message += f'''
{data[0]}({data[1]})
Shares bought yesterday: {data[2]} (+{data[3]}%)
Weight: {data[4]}% (+{data[5]}%)'''
        else:
            message += "\n*(No stocks were bought)*"
        if sending_data['selling'] != []:
            message += "\n*Stocks were sold by the fund:*"
            for data in sending_data['selling']:
                message += f'''
{data[0]}({data[1]})
Shares sold yesterday: {data[2]} (-{data[3]}%)
Weight: {data[4]}% (-{data[5]}%)'''
        else:
            message += "\n*(No stocks were sold)*"
        for user in etf.subscriber.all():
            send_message(message, user.tg_id)
            time.sleep(0.01)
    # except Exception as e:
    #     print(e)
    return True


def handle_stock_add_minus(sending_data, new_company, stock):
    add = True
    share_count = new_company['shares'].values[0]
    if share_count > stock.shares:
        add = True
    elif share_count < stock.shares:
        add = False
    else:
        add = None
    if add is not None:
        stock.shares_delta = (
            (new_company['shares'].values[0]) - (stock.shares))
        stock.shares_delta_percent = Decimal(round(
            (stock.shares_delta/stock.shares), 2))
        stock.shares = new_company['shares'].values[0]
        stock.weight_delta = (
            Decimal(new_company['weight(%)'].values[0]) - (stock.weight))
        stock.weight = new_company['weight(%)'].values[0]
        data = []
        data.append(stock.company)
        data.append(stock.ticker)
        data.append(stock.shares)
        data.append(stock.shares_delta_percent)
        data.append(stock.weight)
        data.append(stock.weight_delta)
        if add:
            sending_data['buying'].append(data)
        else:
            sending_data['selling'].append(data)
    else:
        pass
    return sending_data, stock
