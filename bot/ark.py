from .models import ArkFund, ArkStock, TGUser
from .utils import send_message
import pandas as pd
import requests
import os
import math


def main():
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
                stock = ArkStock.objects.create(
                    company=company, ticker=ticker, shares=shares, weight=weight)
                stock.save()
                fund = ArkFund.objects.get(ticker=fund)
                fund.stocks.add(stock)
                fund.save()
                # data = []
                # append
                # sending_data['added'] =
        removed_stocks = etf.stocks.filter(had_changes=False)
        for stock in removed_stocks:
            sending
            stock.delete()
            pass
        if os.path.exists(f".\{etf.ticker}.csv"):
            os.remove(f".\{etf.ticker}.csv")
        else:
            pass
        # todo send message for all user that subscribed to this fund


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
