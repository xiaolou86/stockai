# -*- coding: utf-8 -*-
from flask import Flask, request, render_template, send_file, jsonify
import matplotlib.pyplot as plt
import io
import akshare as ak
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import pandas as pd
import requests
import json
import base64

from flask_cors import CORS

app = Flask(__name__)
CORS(app)  


@app.route('/high5', methods=['GET', 'POST'])
def high5low5():
    if request.method == 'POST':
        try:
            # Get user input
            # days = float(request.form['days'])
            code = request.form['code']

            stock_zh_a_minute_df = ak.stock_zh_a_minute(symbol=code, period='5')
            #print(stock_zh_a_minute_df)
            minutes = stock_zh_a_minute_df["day"]
            highs = stock_zh_a_minute_df["high"]
            lows = stock_zh_a_minute_df["low"]
            data_len = len(stock_zh_a_minute_df)
            init = False
            highest = 0.0
            highest_minute = "xx"
            highest_ranks = {}

            lowest = 1000000.0
            lowest_minute = "xx"
            lowest_ranks = {}
            
            for i in range(data_len):
                minutes_cur = minutes[i].split(" ")[1]
                # 排除不完整的一天的数据
                if not init:
                    if minutes_cur == "09:35:00":
                        init = True
                    else:
                        continue
                high_cur = float(highs[i])
                if highest < high_cur:
                    highest = high_cur
                    highest_minute = minutes_cur
            
                low_cur = float(lows[i])
                if lowest > low_cur:
                    lowest = low_cur
                    lowest_minute = minutes_cur
                else:
                    pass
            
                # 完整的一天结束了，存放到highest_ranks.
                if minutes_cur == "15:00:00":
                    if highest_minute in highest_ranks:
                        highest_ranks[highest_minute] += 1
                    else:
                        highest_ranks[highest_minute] = 1
                    highest = 0.0
                    if lowest_minute in lowest_ranks:
                        lowest_ranks[lowest_minute] += 1
                    else:
                        lowest_ranks[lowest_minute] = 1
                    lowest = 1000000.0
            
            total_times = 0
            for key, value in highest_ranks.items():
                total_times += value
            print(total_times)
            for key, value in highest_ranks.items():
                highest_ranks[key] = round(value / total_times, 4)
            print(highest_ranks)
            # sort by value in desc
            highest_ranks = {key: value for key, value in sorted(highest_ranks.items(), key=lambda item: item[1], reverse=True)}
            print(highest_ranks)

            total_times = 0
            for key, value in lowest_ranks.items():
                total_times += value
            print(total_times)
            for key, value in lowest_ranks.items():
                lowest_ranks[key] = round(value / total_times, 4)
            print(lowest_ranks)
            lowest_ranks = {key: value for key, value in sorted(lowest_ranks.items(), key=lambda item: item[1], reverse=True)}
            print(lowest_ranks)

            return render_template('high5.html', highest_ranks=highest_ranks, lowest_ranks=lowest_ranks)
        except ValueError:
            return render_template('high5.html', error="Please enter a valid number.")

    return render_template('high5.html')


@app.route('/high', methods=['GET', 'POST'])
def high():
    if request.method == 'POST':
        try:
            # Get user input
            #days = float(request.form['days'])
            code = request.form['code']
            floating_rate = float(request.form['floating_rate'])

            daily_df=ak.stock_zh_a_daily(symbol=code, start_date="20241022", end_date="20251230")
            #print(daily)
            daily_len = len(daily_df)
            dates = daily_df["date"]
            closes = daily_df["close"]
            highs_daily = daily_df["high"]
            dates_datas = {}
            for i in range(daily_len):
                if i == 0:
                    continue;
                close_price = float(closes[i-1])
                high_price = float(highs_daily[i])
                rate = (high_price-close_price)/close_price
                rate_high = rate * (100+floating_rate)/100
                rate_low = rate * (100-floating_rate)/100
                temp = rate_high
                rate_high = max(temp, rate_low)
                rate_low = min(temp, rate_low)

                datesi = str(dates[i])
                dates_datas[datesi] = {}
                dates_datas[datesi]["close"] = closes[i-1]
                dates_datas[datesi]["high"] = highs_daily[i]

                dates_datas[datesi]["range_start"] = close_price * (1+rate_low)
                dates_datas[datesi]["range_end"] = close_price * (1+rate_high)

            print(dates_datas)

            stock_zh_a_minute_df = ak.stock_zh_a_minute(symbol=code, period='1')
            #print(stock_zh_a_minute_df)
            minutes = stock_zh_a_minute_df["day"]
            highs = stock_zh_a_minute_df["high"]
            data_len = len(stock_zh_a_minute_df)
            highest = 0.0
            highest_minute = "xx"
            highest_ranks = {}
            
            for i in range(data_len):
                date_cur = minutes[i].split(" ")[0]
                minutes_cur = minutes[i].split(" ")[1]
            
                high_cur = float(highs[i])
                if date_cur in dates_datas:
                    date_data = dates_datas[date_cur]
                    if high_cur >= date_data["range_start"]:
                        highest_minute = minutes_cur
                        if highest_minute in highest_ranks:
                            highest_ranks[highest_minute] += 1
                        else:
                            highest_ranks[highest_minute] = 1
                else:
                    print("date is wrong")
            
            highest_ranks = {key: highest_ranks[key] for key in sorted(highest_ranks)}
            print(highest_ranks)

            total_times = 0
            for key, value in highest_ranks.items():
                total_times += value
            print(total_times)
            for key, value in highest_ranks.items():
                highest_ranks[key] = round(value / total_times, 3)
            print(highest_ranks)

            # sort by value in desc
            highest_ranks = {key: value for key, value in sorted(highest_ranks.items(), key=lambda item: item[1], reverse=True)}
            print(highest_ranks)

            return render_template('high.html', highest_ranks=highest_ranks, dates_datas=dates_datas)
        except ValueError:
            return render_template('high.html', error="Please enter a valid number.")

    return render_template('high.html')


@app.route('/high/plot.png')
def plot_png2():
    days = float(request.args.get('days', '1'))
    code = request.args.get('code', 'sh000001')

    # Generate the plot again to send the image
    generatePlot(code, days)

    """
    fig, ax = plt.subplots()
    x = [1, 2, 3, 4, 5]
    y = [days * i for i in x]
    ax.plot(x, y)
    ax.set_xlabel('X-axis Label')
    ax.set_ylabel('Y-axis Label')
    ax.set_title(code)
    ax.grid(True)
    """

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return send_file(img, mimetype='image/png')

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/volume_old', methods=['GET', 'POST'])
def volume_old():
    if request.method == 'POST':
        try:
            # Get user input
            days = float(request.form['days'])
            code = request.form['code']


            # Generate the plot
            fig, ax = plt.subplots()
            x = [1, 2, 3, 4, 5]
            y = [days * i for i in x]
            ax.plot(x, y)
            ax.set_xlabel('X-axis Label')
            ax.set_ylabel('Y-axis Label')
            ax.set_title('Plot Title')
            ax.grid(True)

            # Save the plot to a BytesIO object
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plt.close()

            # Extract axes limits
            x_lim = ax.get_xlim()
            y_lim = ax.get_ylim()

            return render_template('volume_old.html', axes=f"1", days=days, code=code)
        except ValueError:
            return render_template('volume_old.html', error="Please enter a valid number.")

    return render_template('volume_old.html')

@app.route('/volume', methods=['GET', 'POST'])
def volume():
    if request.method == 'POST':
        try:
            # Get user input
            days = request.form['days']
            code = request.form['code']
            period = request.form['period']


            # Generate the plot
            fig, ax = plt.subplots()
            x = [1, 2, 3, 4, 5]
            y = [days * i for i in x]
            ax.plot(x, y)
            ax.set_xlabel('X-axis Label')
            ax.set_ylabel('Y-axis Label')
            ax.set_title('Plot Title')
            ax.grid(True)

            # Save the plot to a BytesIO object
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plt.close()

            # Extract axes limits
            x_lim = ax.get_xlim()
            y_lim = ax.get_ylim()

            return render_template('volume.html', axes=f"1", days=days, code=code, period=period)
        except ValueError:
            return render_template('volume.html', error="Please enter a valid number.")

    return render_template('volume.html')

@app.route('/volume1min', methods=['GET', 'POST'])
def volume1min():
    if request.method == 'POST':
        try:
            # Get user input
            days = request.form['days']
            code = request.form['code']

            # Generate the plot
            fig, ax = plt.subplots()
            x = [1, 2, 3, 4, 5]
            y = [days * i for i in x]
            ax.plot(x, y)
            ax.set_xlabel('X-axis Label')
            ax.set_ylabel('Y-axis Label')
            ax.set_title('Plot Title')
            ax.grid(True)

            # Save the plot to a BytesIO object
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plt.close()

            # Extract axes limits
            x_lim = ax.get_xlim()
            y_lim = ax.get_ylim()

            return render_template('volume1min.html', axes=f"1", days=days, code=code)
        except ValueError:
            return render_template('volume1min.html', error="Please enter a valid number.")

    return render_template('volume1min.html')

@app.route('/volume1min.png')
def volume1min_png():
    days = request.args.get('days', '1')
    code = request.args.get('code', 'sh000001')
    period = '1'

    # Generate the plot again to send the image
    if period == '1':
        generateVolume1MinPlot(code, days, period, True)

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return send_file(img, mimetype='image/png')

@app.route('/volume1min-not-sum', methods=['GET', 'POST'])
def volume1min_not_sum():
    if request.method == 'POST':
        try:
            # Get user input
            days = request.form['days']
            code = request.form['code']

            # Generate the plot
            fig, ax = plt.subplots()
            x = [1, 2, 3, 4, 5]
            y = [days * i for i in x]
            ax.plot(x, y)
            ax.set_xlabel('X-axis Label')
            ax.set_ylabel('Y-axis Label')
            ax.set_title('Plot Title')
            ax.grid(True)

            # Save the plot to a BytesIO object
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plt.close()

            # Extract axes limits
            x_lim = ax.get_xlim()
            y_lim = ax.get_ylim()

            return render_template('volume1min-not-sum.html', axes=f"1", days=days, code=code)
        except ValueError:
            return render_template('volume1min-not-sum.html', error="Please enter a valid number.")

    return render_template('volume1min-not-sum.html')

#@app.route('/volume1min_not_sum_png', methods=['GET'])
#def volume1min_not_sum_png():
@app.route('/2')
def home():
        return render_template('2.html')

@app.route('/get_image_json', methods=['GET'])
def get_image_json():
    days = request.args.get('days', '1')
    code = request.args.get('code', 'sh000001')
    period = '1'
    print(days)
    print(code)

    # Generate the plot again to send the image
    time_str="00:00"
    total_str="0"
    if period == '1':
        time_volumes = generateVolume1MinPlot(code, days, period, True, False)

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    encoded_image = base64.b64encode(img.getvalue()).decode('utf-8')

    
    # Combine the image and the data
    data = {
        "image": encoded_image,
        "info":time_volumes 
    }
    
    return jsonify(data)


@app.route('/volume.png')
def volume_png():
    days = request.args.get('days', '1')
    code = request.args.get('code', 'sh000001')
    period = request.args.get('period', '1')

    # Generate the plot again to send the image
    if period == '1':
        generateVolume1MinPlot(code, days, period)
    elif period == '5':
        generateVolume5MinPlot(code, days, period)

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return send_file(img, mimetype='image/png')

@app.route('/plot.png')
def plot_png():
    days = float(request.args.get('days', '1'))
    code = request.args.get('code', 'sh000001')

    # Generate the plot again to send the image
    generatePlot(code, days)

    """
    fig, ax = plt.subplots()
    x = [1, 2, 3, 4, 5]
    y = [days * i for i in x]
    ax.plot(x, y)
    ax.set_xlabel('X-axis Label')
    ax.set_ylabel('Y-axis Label')
    ax.set_title(code)
    ax.grid(True)
    """

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return send_file(img, mimetype='image/png')


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
    time9 = datetime.strptime('09:31:00', '%H:%M:%S')
    print(time9)

    minutes_range1 = pd.date_range(start='09:31:00', end='11:30:00', freq='1min')
    minutes_range2 = pd.date_range(start='13:01:00', end='15:00:00', freq='1min')
    minutes_range = minutes_range1.append(minutes_range2)

    volumes_total = [float(0) for i in range(len(minutes_range))]
    volumes_multiple = [int(0) for i in range(len(minutes_range))]
    volumes_today = [float(0) for i in range(len(minutes_range))]

    today = datetime.today()
    today_date = today.strftime('%Y-%m-%d')

    #stock_zh_a_minute_df = ak.stock_zh_a_minute(symbol='sh000001', period='1', adjust="")
    #print(stock_zh_a_minute_df)
    #minutes = stock_zh_a_minute_df['day']
    #volumes = stock_zh_a_minute_df['volume']

    """
    stock_zh_a_minute_df = bond_zh_hs_cov_min(
        symbol=code,
        period="5",
        adjust="",
        start_date="1979-09-01 09:32:00",
        end_date="2222-01-01 09:32:00",
        ndays=ndays,
    )
    minutes = stock_zh_a_minute_df['时间']
    volumes = stock_zh_a_minute_df['成交额']
    """
    #stock_zh_a_minute_df = ak.stock_zh_a_minute(symbol=code, period="5")
    stock_zh_a_minute_df = stock_zh_a_minute_my(symbol=code, period="1", days=ndays)
    print(stock_zh_a_minute_df)
    minutes = stock_zh_a_minute_df['day']
    volumes = stock_zh_a_minute_df['volume']

    data_len = len(stock_zh_a_minute_df)
    print(data_len)
    for i in range(data_len):
        time_cur = datetime.strptime(minutes[i].split(" ")[1], '%H:%M:%S')
        offset_in_minutes = time_cur-time9
        index = offset_in_minutes.total_seconds() / 60 / 1
        index = int(index)
        # if it's in the afternoon, need to minus "1 hour and a half"
        if index >= 60*2:
            index = index - 60 - 30
        if minutes[i].split(" ")[0] == today_date:
            # today's data
            volumes_today[index] = float(volumes[i])
        else:
            # history's data
            volumes_total[index] += float(volumes[i])
            volumes_multiple[index] += 1

    # calc the average
    minutes_range_len = len(minutes_range)
    today_latest_index = 0

    # 去掉头尾
    begin_one = 1
    last_one = minutes_range_len-2
    for i in range(0, last_one+1):
        if volumes_multiple[i] >= 1:
            volumes_total[i] = volumes_total[i]/volumes_multiple[i]
        if i <= begin_one:
            pass
        else:
            volumes_total[i] += volumes_total[i-1]
            if volumes_today[i] == 0 and today_latest_index == 0:
                today_latest_index = i-1
            else:
                volumes_today[i] += volumes_today[i-1]

    # 今天结束了
    if today_latest_index == 0 and volumes_today[0] != 0:
        today_latest_index = minutes_range_len-2

    ####### no need to calc phase1 and phase3
    total_phase2_latest = volumes_total[today_latest_index]
    total_phase2_all = volumes_total[last_one]
    print(total_phase2_latest)
    print(total_phase2_all)

    if today_latest_index < 1:
        # time is <= 9:30 or >= 15:00
        pass

    for i in range(begin_one, today_latest_index+1):
        #这个值保存的是当下时间点估计的交易总额
        volumes_today[i] = 1.0*total_phase2_all/volumes_total[i]*volumes_today[i] + volumes_today[0] + volumes_total[minutes_range_len-1]

    today_phase2_all = volumes_today[today_latest_index]
    # 直接取之前的,不按比例
    print(today_phase2_all)

    if not isSum:
        # 去掉头尾，为了减少曲线的取值区间
        volumes_today[0] = volumes_today[begin_one]
        volumes_today[minutes_range_len-1] = volumes_today[last_one-1]
        volumes_today[minutes_range_len-2] = volumes_today[last_one-1]

    """
    ####### ok to calc phase1 and phase3
    total_phase1 = volumes_total[0]
    total_phase2_latest = volumes_total[today_latest_index] - total_phase1
    total_phase2_all = volumes_total[minutes_range_len-2] - total_phase1
    total_phase3 = volumes_total[minutes_range_len-1] - volumes_total[minutes_range_len-2]
    print(total_phase1)
    print(total_phase2_latest)
    print(total_phase2_all)
    print(total_phase3)
    print(volumes_total[minutes_range_len-1])

    today_phase1 = volumes_today[0]
    today_phase2_latest = volumes_today[today_latest_index] - today_phase1

    if today_latest_index < 1:
        # time is <= 9:30 or >= 15:00
        pass
    else:
        # the other time
        if isFillRemaining:
            # 按比例估算
            rate = today_phase2_latest*1.0/total_phase2_latest
            for i in range(today_latest_index+1, minutes_range_len-1):
                volumes_today[i] = rate*(volumes_total[i]-total_phase1) + today_phase1

            # phase3: assumed to equal to total_phase3
            volumes_today[minutes_range_len-1] = volumes_today[minutes_range_len-2] + total_phase3

    today_phase2_all = 1.0*today_phase2_latest/total_phase2_latest*total_phase2_all
    # 直接取之前的,不按比例
    today_phase3 = total_phase3
    print(today_phase1)
    print(today_phase2_latest)
    print(today_phase2_all)
    print(today_phase3)
    print(volumes_today[minutes_range_len-1])

    if not isSum:
        for i in range(minutes_range_len-1, 0, -1):
            volumes_total[i] -= volumes_total[i-1]
            volumes_today[i] -= volumes_today[i-1]

        # 去掉头尾
        volumes_today[0] = 0
        volumes_today[1] = 0
        volumes_today[2] = 0
        volumes_today[minutes_range_len-1] = 0
        volumes_today[minutes_range_len-2] = 0
        volumes_today[minutes_range_len-3] = 0
        volumes_today[minutes_range_len-4] = 0
    """

    df = pd.DataFrame(minutes_range, columns=['timestamp'])
    df['volumes_total'] = volumes_total
    df['volumes_today'] = volumes_today


    # Set the 'timestamp' column as the index
    df.set_index('timestamp', inplace=True)

    #print("Original DataFrame:")
    #print(df)

    # Define the time ranges to remove
    drop_ranges = [
        (pd.Timestamp('11:31:00'), pd.Timestamp('12:59:00')),
        (pd.Timestamp('09:00:00'), pd.Timestamp('09:14:00'))
    ]
    # Remove the specified time ranges
    for start_time, end_time in drop_ranges:
        print(start_time)
        df = df.drop(df[start_time:end_time].index)

    print("\nDataFrame after removing specified time range:")
    #print(df)

    # Plotting the data
    plt.figure(figsize=(18, 8))

    """
    # Set the Chinese font
    plt.rcParams['font.sans-serif'] = ['AR PL UMing CN']  # Specify the font family
    plt.rcParams['axes.unicode_minus'] = False  # Ensure minus sign is displayed correctly
    """

    ### Plot
    #plt.plot(use_index=True, y='volumes_total', marker='o', linestyle='-')
    #plt.plot(use_index=True, y='volumes_today', marker='o', linestyle='-')
    #df.plot(y='volumes_total', use_index=True, marker='o', linestyle='-')
    #df.plot(y='volumes_today', use_index=True, marker='o', linestyle='-')

    #plt.plot(df.index, df['volumes_total'], marker='.', markersize=2, linestyle='-', label="n days' average volume (1 minutes)")
    plt.plot(df.index, df['volumes_today'], marker='.', markersize=2, linestyle='-', label="today volume (1 minutes)")

    """
    plt.plot(df["timestamp"], df['volumes_total'], marker='o', linestyle='-', label="n days' average")
    plt.plot(df["timestamp"], df['volumes_today'], marker='o', linestyle='-', label="today's value")
    """

    # Customize the x-axis ticks
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=1))  # Adjust the interval as needed


    # Custom ticks and labels
    all_ticks = minutes_range
    tick_labels = [tick.strftime('%H:%M') for tick in minutes_range]

    # Set custom ticks and labels
    plt.xticks(ticks=all_ticks, labels=tick_labels, rotation=45)



    ## Create a plot
    ##plt.plot(x, y)
    ##plt.plot(x, y2)
    #plt.plot(minutes, transaction_amounts, marker='o', linestyle='-')
    ## Customize the x-axis ticks
    #plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    #plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
    #plt.gcf().autofmt_xdate()  # Rotate and align the x-axis labels


    # Customize the plot to display axes
    plt.grid(True)  # Show grid lines
    plt.xlabel('timestamp')
    plt.ylabel('volume')
    title = code
    if isSum:
        title = title + "    Today's volume may be: " + str(today_phase2_all)
    now = datetime.now()
    time_str = now.strftime('%H:%M') 

    daily_df=ak.stock_zh_a_daily(symbol=code, start_date="20241201", end_date="20251230")
    #print(daily)
    daily_len = len(daily_df)
    print(daily_df)

    today = datetime.now()
    yesterday = today - timedelta(days=1)

    yesterday_volume = 0
    today_all_volume = 0
    for i in range(0, daily_len):
        if yesterday.date() == daily_df["date"][i]:
            yesterday_volume = daily_df["volume"][i]
            print(yesterday_volume)
        elif today.date() == daily_df["date"][i]:
            today_all_volume = daily_df["volume"][i]
            print(today_all_volume)

    for i in range(0, minutes_range_len):
        volumes_today[i] = round(volumes_today[i]/1000000, 0)
    time_volumes = {
            "昨日总量": round(yesterday_volume/1000000, 0),
            "09:35": volumes_today[5],
            "09:45": volumes_today[15],
            "10:00": volumes_today[30],
            "10:15": volumes_today[45],
            "10:30": volumes_today[60],
            "10:45": volumes_today[75],
            "11:00": volumes_today[90],
            "11:15": volumes_today[105],
            "11:27": volumes_today[117],
            "13:05": volumes_today[126],
            "13:15": volumes_today[136],
            "13:30": volumes_today[151],
            "13:45": volumes_today[166],
            "14:00": volumes_today[181],
            "14:15": volumes_today[196],
            "14:30": volumes_today[211],
            "14:45": volumes_today[226],
            "14:54": volumes_today[235],
            #"今日当前总成交量": today_phase2_all,
            "今日总量": round(today_all_volume/1000000, 0),
    }


    plt.title(title)

    plt.legend()

    plt.gcf().autofmt_xdate()  # Rotate and format x-axis labels for better readability

    # Show the plot
    plt.tight_layout()
    plt.show(block=True)
    return time_volumes

def generateVolume5MinPlot(code, ndays, period):
    time9 = datetime.strptime('09:35:00', '%H:%M:%S')
    print(time9)

    minutes_range1 = pd.date_range(start='09:35:00', end='11:30:00', freq='5min')
    minutes_range2 = pd.date_range(start='13:05:00', end='15:00:00', freq='5min')
    minutes_range = minutes_range1.append(minutes_range2)

    volumes_total = [float(0) for i in range(len(minutes_range))]
    volumes_multiple = [int(0) for i in range(len(minutes_range))]
    volumes_today = [float(0) for i in range(len(minutes_range))]

    today = datetime.today()
    today_date = today.strftime('%Y-%m-%d')

    #stock_zh_a_minute_df = ak.stock_zh_a_minute(symbol='sh000001', period='1', adjust="")
    #print(stock_zh_a_minute_df)
    #minutes = stock_zh_a_minute_df['day']
    #volumes = stock_zh_a_minute_df['volume']

    """
    stock_zh_a_minute_df = bond_zh_hs_cov_min(
        symbol=code,
        period="5",
        adjust="",
        start_date="1979-09-01 09:32:00",
        end_date="2222-01-01 09:32:00",
        ndays=ndays,
    )
    minutes = stock_zh_a_minute_df['时间']
    volumes = stock_zh_a_minute_df['成交额']
    """
    #stock_zh_a_minute_df = ak.stock_zh_a_minute(symbol=code, period="5")
    stock_zh_a_minute_df = stock_zh_a_minute_my(symbol=code, period="5", days=ndays)
    print(stock_zh_a_minute_df)
    minutes = stock_zh_a_minute_df['day']
    volumes = stock_zh_a_minute_df['volume']

    data_len = len(stock_zh_a_minute_df)
    print(data_len)
    for i in range(data_len):
        time_cur = datetime.strptime(minutes[i].split(" ")[1], '%H:%M:%S')
        offset_in_minutes = time_cur-time9
        index = offset_in_minutes.total_seconds() / 60 / 5
        index = int(index)
        # if it's in the afternoon, need to minus "1 hour and a half"
        if index >= 12*2:
            index = index - 12 - 6
        if minutes[i].split(" ")[0] == today_date:
            # today's data
            volumes_today[index] = float(volumes[i])
        else:
            # history's data
            volumes_total[index] += float(volumes[i])
            volumes_multiple[index] += 1

    # calc the average
    minutes_range_len = len(minutes_range)
    today_latest_index = 0
    for i in range(minutes_range_len):
        if volumes_multiple[i] >= 1:
            volumes_total[i] = volumes_total[i]/volumes_multiple[i]
        if i == 0:
            pass
        else:
            volumes_total[i] += volumes_total[i-1]
            if volumes_today[i] == 0 and today_latest_index == 0:
                today_latest_index = i-1
            else:
                volumes_today[i] += volumes_today[i-1]

    # 有可能今天结束了
    if today_latest_index == 0:
        today_latest_index = minutes_range_len-2

    total_phase1 = volumes_total[0]
    total_phase2_latest = volumes_total[today_latest_index] - total_phase1
    total_phase2_all = volumes_total[minutes_range_len-2] - total_phase1
    total_phase3 = volumes_total[minutes_range_len-1] - volumes_total[minutes_range_len-2]
    print(total_phase1)
    print(total_phase2_latest)
    print(total_phase2_all)
    print(total_phase3)
    print(volumes_total[minutes_range_len-1])

    today_phase1 = volumes_today[0]
    today_phase2_latest = volumes_today[today_latest_index] - today_phase1
    # 按比例估算
    today_phase2_all = 1.0*today_phase2_latest/(total_phase2_latest*1.0/total_phase2_all)
    # 直接取之前的,不按比例
    today_phase3 = total_phase3
    print(today_phase1)
    print(today_phase2_latest)
    print(today_phase2_all)
    print(today_phase3)
    print(volumes_today[minutes_range_len-1])


    df = pd.DataFrame(minutes_range, columns=['timestamp'])
    df['volumes_total'] = volumes_total
    df['volumes_today'] = volumes_today


    # Set the 'timestamp' column as the index
    df.set_index('timestamp', inplace=True)

    #print("Original DataFrame:")
    #print(df)

    # Define the time ranges to remove
    drop_ranges = [
        (pd.Timestamp('11:31:00'), pd.Timestamp('12:59:00')),
        (pd.Timestamp('09:00:00'), pd.Timestamp('09:14:00'))
    ]
    # Remove the specified time ranges
    for start_time, end_time in drop_ranges:
        print(start_time)
        df = df.drop(df[start_time:end_time].index)

    print("\nDataFrame after removing specified time range:")
    #print(df)

    # Plotting the data
    plt.figure(figsize=(18, 8))

    """
    # Set the Chinese font
    plt.rcParams['font.sans-serif'] = ['AR PL UMing CN']  # Specify the font family
    plt.rcParams['axes.unicode_minus'] = False  # Ensure minus sign is displayed correctly
    """

    ### Plot
    #plt.plot(use_index=True, y='volumes_total', marker='o', linestyle='-')
    #plt.plot(use_index=True, y='volumes_today', marker='o', linestyle='-')
    #df.plot(y='volumes_total', use_index=True, marker='o', linestyle='-')
    #df.plot(y='volumes_today', use_index=True, marker='o', linestyle='-')

    plt.plot(df.index, df['volumes_total'], marker='o', linestyle='-', label="n days' average volume (5 minutes)")
    plt.plot(df.index, df['volumes_today'], marker='o', linestyle='-', label="today volume (5 minutes)")

    """
    plt.plot(df["timestamp"], df['volumes_total'], marker='o', linestyle='-', label="n days' average")
    plt.plot(df["timestamp"], df['volumes_today'], marker='o', linestyle='-', label="today's value")
    """

    # Customize the x-axis ticks
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=5))  # Adjust the interval as needed


    # Custom ticks and labels
    all_ticks = minutes_range
    tick_labels = [tick.strftime('%H:%M') for tick in minutes_range]

    # Set custom ticks and labels
    plt.xticks(ticks=all_ticks, labels=tick_labels, rotation=45)



    ## Create a plot
    ##plt.plot(x, y)
    ##plt.plot(x, y2)
    #plt.plot(minutes, transaction_amounts, marker='o', linestyle='-')
    ## Customize the x-axis ticks
    #plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    #plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
    #plt.gcf().autofmt_xdate()  # Rotate and align the x-axis labels


    # Customize the plot to display axes
    plt.grid(True)  # Show grid lines
    plt.xlabel('timestamp')
    plt.ylabel('volume')
    title = code
    title = title + "    Today's volume may be: " + str(today_phase1+today_phase2_all+today_phase3)
    plt.title(title)

    plt.legend()

    plt.gcf().autofmt_xdate()  # Rotate and format x-axis labels for better readability

    # Show the plot
    plt.tight_layout()
    plt.show(block=True)

def generatePlot(code, ndays):
    time9 = datetime.strptime('09:35:00', '%H:%M:%S')
    print(time9)

    minutes_range1 = pd.date_range(start='09:35:00', end='11:30:00', freq='5min')
    minutes_range2 = pd.date_range(start='13:05:00', end='15:00:00', freq='5min')
    minutes_range = minutes_range1.append(minutes_range2)

    volumes_total = [float(0) for i in range(len(minutes_range))]
    volumes_multiple = [int(0) for i in range(len(minutes_range))]
    volumes_today = [float(0) for i in range(len(minutes_range))]

    today = datetime.today()
    today_date = today.strftime('%Y-%m-%d')

    #stock_zh_a_minute_df = ak.stock_zh_a_minute(symbol='sh000001', period='1', adjust="")
    #print(stock_zh_a_minute_df)
    #minutes = stock_zh_a_minute_df['day']
    #volumes = stock_zh_a_minute_df['volume']

    stock_zh_a_minute_df = bond_zh_hs_cov_min(
        symbol=code,
        period="5",
        adjust="",
        start_date="1979-09-01 09:32:00",
        end_date="2222-01-01 09:32:00",
        ndays=ndays,
    )
    print(stock_zh_a_minute_df)

    minutes = stock_zh_a_minute_df['时间']
    volumes = stock_zh_a_minute_df['成交额']
    data_len = len(stock_zh_a_minute_df)
    for i in range(data_len):
        time_cur = datetime.strptime(minutes[i].split(" ")[1], '%H:%M:%S')
        offset_in_minutes = time_cur-time9
        index = offset_in_minutes.total_seconds() / 60 / 5
        index = int(index)
        # if it's in the afternoon, need to minus "1 hour and a half"
        if index >= 12*2:
            index = index - 12 - 6
        if minutes[i].split(" ")[0] == today_date:
            # today's data
            volumes_today[index] = float(volumes[i])
        else:
            # history's data
            volumes_total[index] += float(volumes[i])
            volumes_multiple[index] += 1

    # calc the average
    for i in range(len(minutes_range)):
        if volumes_multiple[i] >= 1:
            volumes_total[i] = volumes_total[i]/volumes_multiple[i]


    df = pd.DataFrame(minutes_range, columns=['timestamp'])
    df['volumes_total'] = volumes_total
    df['volumes_today'] = volumes_today


    # Set the 'timestamp' column as the index
    df.set_index('timestamp', inplace=True)

    print("Original DataFrame:")
    print(df)

    # Define the time ranges to remove
    drop_ranges = [
        (pd.Timestamp('11:31:00'), pd.Timestamp('12:59:00')),
        (pd.Timestamp('09:00:00'), pd.Timestamp('09:14:00'))
    ]
    # Remove the specified time ranges
    for start_time, end_time in drop_ranges:
        print(start_time)
        df = df.drop(df[start_time:end_time].index)

    print("\nDataFrame after removing specified time range:")
    print(df)

    # Plotting the data
    plt.figure(figsize=(18, 8))

    """
    # Set the Chinese font
    plt.rcParams['font.sans-serif'] = ['AR PL UMing CN']  # Specify the font family
    plt.rcParams['axes.unicode_minus'] = False  # Ensure minus sign is displayed correctly
    """

    ### Plot
    #plt.plot(use_index=True, y='volumes_total', marker='o', linestyle='-')
    #plt.plot(use_index=True, y='volumes_today', marker='o', linestyle='-')
    #df.plot(y='volumes_total', use_index=True, marker='o', linestyle='-')
    #df.plot(y='volumes_today', use_index=True, marker='o', linestyle='-')

    plt.plot(df.index, df['volumes_total'], marker='o', linestyle='-', label="n days' average volume (5 minutes)")
    plt.plot(df.index, df['volumes_today'], marker='o', linestyle='-', label="today volume (5 minutes)")

    """
    plt.plot(df["timestamp"], df['volumes_total'], marker='o', linestyle='-', label="n days' average")
    plt.plot(df["timestamp"], df['volumes_today'], marker='o', linestyle='-', label="today's value")
    """

    # Customize the x-axis ticks
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=5))  # Adjust the interval as needed


    # Custom ticks and labels
    all_ticks = minutes_range
    tick_labels = [tick.strftime('%H:%M') for tick in minutes_range]

    # Set custom ticks and labels
    plt.xticks(ticks=all_ticks, labels=tick_labels, rotation=45)



    ## Create a plot
    ##plt.plot(x, y)
    ##plt.plot(x, y2)
    #plt.plot(minutes, transaction_amounts, marker='o', linestyle='-')
    ## Customize the x-axis ticks
    #plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    #plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
    #plt.gcf().autofmt_xdate()  # Rotate and align the x-axis labels


    # Customize the plot to display axes
    plt.grid(True)  # Show grid lines
    plt.xlabel('timestamp')
    plt.ylabel('volume (unit: yuan)')
    plt.title(code)

    plt.legend()

    plt.gcf().autofmt_xdate()  # Rotate and format x-axis labels for better readability

    # Show the plot
    plt.tight_layout()
    plt.show(block=True)


@app.route('/stock_individual_info', methods=['GET', 'POST'])
def stock_individual_info():
    if request.method == 'POST':
        try:
            code = request.form['code']
            stock_individual_info_em_df = ak.stock_individual_info_em(symbol=code)
            html_table = stock_individual_info_em_df.to_html(index=False)

            return render_template('stock_individual_info.html', individual_info=html_table)
        except ValueError:
            return render_template('stock_individual_info.html')
    return render_template('stock_individual_info.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=50080)

