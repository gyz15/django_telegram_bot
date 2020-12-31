from .models import ArkFund, ArkStock, TGUser
from .utils import send_message
import pandas as pd
import requests
import os


def main():
    for etf in ArkFund.objects.all():
        sending_data = {"added": [], "removed": [],
                        "buying": [], "selling": []}
        with requests.get(etf.file_url, stream=True) as r:
            with open(f".\{etf.ticker}.csv", "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        new_data = pd.read_csv(
            f".\{etf.ticker}.csv", parse_dates=[0], dayfirst=True)
        # comparing
        for company_name in new_data.company:
            try:
                stock = etf.stocks.get(company=company_name)
                if new_data.loc[new_data.company == company_name]['shares'] != stock.shares:
                    # owh oh, fund manager added or decrease the share amount that they hold
                    # hanlde increase/decrease of shares
                    # add to the message to sent to user
                    pass
                else:
                    # no changes on stock, passs
                    pass
                stock.had_changes = True
                stock.save()
            except ArkStock.DoesNotExist:
                # New stock added, handle it(database)
                # And also message
                pass
        removed_stocks = etf.stocks.filter(had_changes=False)
        for stock in removed_stocks:
            # do something for removed stocks
            pass
        if os.path.exists(f".\{etf.ticker}.csv"):
            os.remove(f".\{etf.ticker}.csv")
        else:
            pass
            # raise an error or send a message to admin
