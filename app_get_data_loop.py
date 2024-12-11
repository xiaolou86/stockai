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



# 能处理5分钟的情况，但1分钟的只有660条数据
def bond_zh_hs_cov_min(
    symbol: str = "sz128039",
    period: str = "15",
    adjust: str = "",
    start_date: str = "1979-09-01 09:32:00",
    end_date: str = "2222-01-01 09:32:00",
    ndays: int = 1,
) -> pd.DataFrame:
    """
    东方财富网-可转债-分时行情
    https://quote.eastmoney.com/concept/sz128039.html
    :param symbol: 转债代码
    :type symbol: str
    :param period: choice of {'1', '5', '15', '30', '60'}
    :type period: str
    :param adjust: choice of {'', 'qfq', 'hfq'}
    :type adjust: str
    :param start_date: 开始日期
    :type start_date: str
    :param end_date: 结束日期
    :type end_date: str
    :return: 分时行情
    :rtype: pandas.DataFrame
    """
    market_type = {"sh": "1", "sz": "0"}
    if period == "1":
        url = "https://push2.eastmoney.com/api/qt/stock/trends2/get"
        params = {
            "secid": f"{market_type[symbol[:2]]}.{symbol[2:]}",
            "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
            "iscr": "0",
            "iscca": "0",
            "ut": "f057cbcbce2a86e2866ab8877db1d059",
            "ndays": "1",
            #"lmt": "660",
            #"smplmt": "460"
        }
        r = requests.get(url, params=params)
        data_json = r.json()
        temp_df = pd.DataFrame(
            [item.split(",") for item in data_json["data"]["trends"]]
        )
        temp_df.columns = [
            "时间",
            "开盘",
            "收盘",
            "最高",
            "最低",
            "成交量",
            "成交额",
            "最新价",
        ]
        temp_df.index = pd.to_datetime(temp_df["时间"])
        temp_df = temp_df[start_date:end_date]
        temp_df.reset_index(drop=True, inplace=True)
        temp_df["开盘"] = pd.to_numeric(temp_df["开盘"], errors="coerce")
        temp_df["收盘"] = pd.to_numeric(temp_df["收盘"], errors="coerce")
        temp_df["最高"] = pd.to_numeric(temp_df["最高"], errors="coerce")
        temp_df["最低"] = pd.to_numeric(temp_df["最低"], errors="coerce")
        temp_df["成交量"] = pd.to_numeric(temp_df["成交量"], errors="coerce")
        temp_df["成交额"] = pd.to_numeric(temp_df["成交额"], errors="coerce")
        temp_df["最新价"] = pd.to_numeric(temp_df["最新价"], errors="coerce")
        temp_df["时间"] = pd.to_datetime(temp_df["时间"]).astype(
            str
        )  # show datatime here
        return temp_df
    else:
        adjust_map = {
            "": "0",
            "qfq": "1",
            "hfq": "2",
        }
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        params = {
            "secid": f"{market_type[symbol[:2]]}.{symbol[2:]}",
            "klt": period,
            "fqt": adjust_map[adjust],
            "lmt": str((ndays+1)*48),
            "end": "20500000",
            "iscca": "1",
            "fields1": "f1,f2,f3,f4,f5",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "forcect": "1",
        }
        r = requests.get(url, params=params)
        data_json = r.json()
        temp_df = pd.DataFrame(
            [item.split(",") for item in data_json["data"]["klines"]]
        )
        temp_df.columns = [
            "时间",
            "开盘",
            "收盘",
            "最高",
            "最低",
            "成交量",
            "成交额",
            "振幅",
            "涨跌幅",
            "涨跌额",
            "换手率",
        ]
        temp_df.index = pd.to_datetime(temp_df["时间"])
        temp_df = temp_df[start_date:end_date]
        temp_df.reset_index(drop=True, inplace=True)
        temp_df["开盘"] = pd.to_numeric(temp_df["开盘"], errors="coerce")
        temp_df["收盘"] = pd.to_numeric(temp_df["收盘"], errors="coerce")
        temp_df["最高"] = pd.to_numeric(temp_df["最高"], errors="coerce")
        temp_df["最低"] = pd.to_numeric(temp_df["最低"], errors="coerce")
        temp_df["成交量"] = pd.to_numeric(temp_df["成交量"], errors="coerce")
        temp_df["成交额"] = pd.to_numeric(temp_df["成交额"], errors="coerce")
        temp_df["振幅"] = pd.to_numeric(temp_df["振幅"], errors="coerce")
        temp_df["涨跌幅"] = pd.to_numeric(temp_df["涨跌幅"], errors="coerce")
        temp_df["涨跌额"] = pd.to_numeric(temp_df["涨跌额"], errors="coerce")
        temp_df["换手率"] = pd.to_numeric(temp_df["换手率"], errors="coerce")
        temp_df["时间"] = pd.to_datetime(temp_df["时间"]).astype(str)
        temp_df = temp_df[
            [
                "时间",
                "开盘",
                "收盘",
                "最高",
                "最低",
                "涨跌幅",
                "涨跌额",
                "成交量",
                "成交额",
                "振幅",
                "换手率",
            ]
        ]
        return temp_df


def stock_zh_a_minute_my(
    symbol: str = "sh000001", period: str = "5", adjust: str = "", days: str = "1"
) -> pd.DataFrame:
    """
    股票及股票指数历史行情数据-分钟数据
    https://finance.sina.com.cn/realstock/company/sh600519/nc.shtml
    :param symbol: sh000300
    :type symbol: str
    :param period: 1, 5, 15, 30, 60 分钟的数据
    :type period: str
    :param adjust: 默认为空: 返回不复权的数据; qfq: 返回前复权后的数据; hfq: 返回后复权后的数据;
    :type adjust: str
    :return: specific data
    :rtype: pandas.DataFrame
    """
    url = (
        "https://quotes.sina.cn/cn/api/jsonp_v2.php/=/CN_MarketDataService.getKLineData"
    )
    iperiod = int(period)
    datalen = 60*4/iperiod*(int(days)+1)
    datalen = min(datalen, 1970)
    params = {
        "symbol": symbol,
        "scale": period,
        "ma": "no",
        #"datalen": "1970",
        "datalen": datalen,
    }
    r = requests.get(url, params=params)
    data_text = r.text
    try:
        data_json = json.loads(data_text.split("=(")[1].split(");")[0])
        temp_df = pd.DataFrame(data_json).iloc[:, :7]
    except:  # noqa: E722
        url = f"https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_{symbol}_{period}_1658852984203=/CN_MarketDataService.getKLineData"
        params = {
            "symbol": symbol,
            "scale": period,
            "ma": "no",
            "datalen": datalen,
        }
        r = requests.get(url, params=params)
        data_text = r.text
        data_json = json.loads(data_text.split("=(")[1].split(");")[0])
        temp_df = pd.DataFrame(data_json).iloc[:, :7]
    if temp_df.empty:
        print(f"{symbol} 股票数据不存在，请检查是否已退市")
        return pd.DataFrame()
    try:
        stock_zh_a_daily(symbol=symbol, adjust="qfq")
    except:  # noqa: E722
        return temp_df

    if adjust == "":
        return temp_df

    if adjust == "qfq":
        temp_df[["date", "time"]] = temp_df["day"].str.split(" ", expand=True)
        # 处理没有最后一分钟的情况
        need_df = temp_df[
            [
                True if "09:31:00" <= item <= "15:00:00" else False
                for item in temp_df["time"]
            ]
        ]
        need_df.drop_duplicates(subset=["date"], keep="last", inplace=True)
        need_df.index = pd.to_datetime(need_df["date"])
        stock_zh_a_daily_qfq_df = stock_zh_a_daily(symbol=symbol, adjust="qfq")
        stock_zh_a_daily_qfq_df.index = pd.to_datetime(stock_zh_a_daily_qfq_df["date"])
        result_df = stock_zh_a_daily_qfq_df.iloc[-len(need_df) :, :]["close"].astype(
            float
        ) / need_df["close"].astype(float)
        temp_df.index = pd.to_datetime(temp_df["date"])
        merged_df = pd.merge(temp_df, result_df, left_index=True, right_index=True)
        merged_df["open"] = merged_df["open"].astype(float) * merged_df["close_y"]
        merged_df["high"] = merged_df["high"].astype(float) * merged_df["close_y"]
        merged_df["low"] = merged_df["low"].astype(float) * merged_df["close_y"]
        merged_df["close"] = merged_df["close_x"].astype(float) * merged_df["close_y"]
        temp_df = merged_df[["day", "open", "high", "low", "close", "volume"]]
        temp_df.reset_index(drop=True, inplace=True)
        return temp_df
    if adjust == "hfq":
        temp_df[["date", "time"]] = temp_df["day"].str.split(" ", expand=True)
        # 处理没有最后一分钟的情况
        need_df = temp_df[
            [
                True if "09:31:00" <= item <= "15:00:00" else False
                for item in temp_df["time"]
            ]
        ]
        need_df.drop_duplicates(subset=["date"], keep="last", inplace=True)
        need_df.index = pd.to_datetime(need_df["date"])
        stock_zh_a_daily_hfq_df = stock_zh_a_daily(symbol=symbol, adjust="hfq")
        stock_zh_a_daily_hfq_df.index = pd.to_datetime(stock_zh_a_daily_hfq_df["date"])
        result_df = stock_zh_a_daily_hfq_df.iloc[-len(need_df) :, :]["close"].astype(
            float
        ) / need_df["close"].astype(float)
        temp_df.index = pd.to_datetime(temp_df["date"])
        merged_df = pd.merge(temp_df, result_df, left_index=True, right_index=True)
        merged_df["open"] = merged_df["open"].astype(float) * merged_df["close_y"]
        merged_df["high"] = merged_df["high"].astype(float) * merged_df["close_y"]
        merged_df["low"] = merged_df["low"].astype(float) * merged_df["close_y"]
        merged_df["close"] = merged_df["close_x"].astype(float) * merged_df["close_y"]
        temp_df = merged_df[["day", "open", "high", "low", "close", "volume"]]
        temp_df.reset_index(drop=True, inplace=True)
        return temp_df

def generateVolume1MinPlot(code, ndays, period, isFillRemaining=False, isSum=True):

    #stock_zh_a_minute_df = ak.stock_zh_a_minute(symbol=code, period="5")
    stock_zh_a_minute_df = stock_zh_a_minute_my(symbol=code, period="1", days=ndays)
    print(stock_zh_a_minute_df)
    minutes = stock_zh_a_minute_df['day']
    volumes = stock_zh_a_minute_df['volume']

    filename = code + ".csv"
    stock_zh_a_minute_df.to_csv(filename, mode='a', header=False, index=False)


def my_function():
    code = "sh000001"
    generateVolume1MinPlot(code, 1, "1")

if __name__ == '__main__':
    # Schedule the function to run every 1 day
    schedule.every(1).days.at("00:00").do(my_function)  # Change time as needed

    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(1)  # Sleep to avoid high CPU usage
