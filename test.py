# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import io
import akshare as ak
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import pandas as pd
import requests
import json
import base64
import schedule
import time



def my_function():
    stock_individual_info_em_df = ak.stock_individual_info_em(symbol="002747")
    print(stock_individual_info_em_df)


    stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol="002747", period="daily", start_date="20200101", end_date='20250528', adjust="")
    print(stock_zh_a_hist_df)

if __name__ == '__main__':
    my_function()
