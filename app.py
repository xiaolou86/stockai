# -*- coding: utf-8 -*-
from flask import Flask, request, render_template, send_file
import matplotlib.pyplot as plt
import io
import akshare as ak
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import pandas as pd
import requests

app = Flask(__name__)


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
    days = float(request.args.get('days', 1))
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

@app.route('/', methods=['GET', 'POST'])
def index():
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

            return render_template('index.html', axes=f"1", days=days, code=code)
        except ValueError:
            return render_template('index.html', error="Please enter a valid number.")

    return render_template('index.html')

@app.route('/plot.png')
def plot_png():
    days = float(request.args.get('days', 1))
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=50080)

