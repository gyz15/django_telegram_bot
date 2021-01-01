from .models import ArkFund, ArkStock, TGUser
from .utils import send_message
import pandas as pd
import requests
import os
import math
from .utils import send_message
import time
from datetime import date, timedelta


def find_ark():
    try:
        for etf in ArkFund.objects.all():
            with requests.get(etf.file_url, stream=True) as r:
                with open(f".\{etf.ticker}.csv", "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            new_data = pd.read_csv(
                f".\{etf.ticker}.csv", parse_dates=[0], dayfirst=True)
            sending_data = {"added": [], "removed": [],
                            "buying": [], "selling": []}
            # Comparing latest data with the data in the database
            for company_name in new_data.company:
                new_company = new_data.loc[new_data.company == company_name]
                try:
                    stock = etf.stocks.get(company=company_name)
                    sending_data, stock = handle_stock_add_minus(
                        sending_data, new_company, stock)
                    stock.had_changes = True
                    stock.save()
                except ArkStock.DoesNotExist:
                    # todo handle message here
                    fund = new_company['fund']
                    company = new_company['company']
                    ticker = new_company['ticker']
                    shares = new_company['shares']
                    weight = new_company['weight(%)']
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
            date = date.today() - timedelta(days=1)
            date_val = date.strftime('%d/%m/%y')
            message = f'Changes of {fund} on {date_val}:'
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
                send_markdown_stock(message, user.tg_id)
                time.sleep(0.01)
    except Exception as e:
        print(e)
    return True


def handle_stock_add_minus(sending_data, new_company, stock):
    add = True
    if new_company['shares'] > stock.shares:
        add = True
    elif new_company['shares'] < stock.shares:
        add = False
    else:
        add = None
    if add is not None:
        stock.shares_delta = (
            (new_company['shares']) - (stock.shares))
        stock.shares_delta_percent = (
            math.round(stock.shares_delta/stock.shares), 2)
        stock.shares = new_company['shares']
        stock.weight_delta = (
            (new_company['weight(%)']) - (stock.weight))
        stock.weight = new_company['weight(%)']
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
