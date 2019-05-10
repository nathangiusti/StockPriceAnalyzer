from yahoo_fin.stock_info import *
import datetime
import csv
import sys

BUY_MULTIPLIER = 2
SELL_MULTIPLIER = 1
STOCK_RETRY = 3

ORDER_CAP = 1000


class Stock:
    def __init__(self, ticker, price, mean, std_dev, margin):
        self.ticker = ticker
        self.price = price
        self.mean = mean
        self.std_dev = std_dev
        self.margin = margin


def calculate_mean(data_list):
    sum = 0
    weight = 0
    for x in range(len(data_list) + 1):
        weight += x

    i = 1
    for val in data_list:
        sum += val * i / weight
        i += 1
    return sum


def get_bought_info(stock, bought_list):
    for entry in bought_list:
        if entry[0] == stock:
            return entry[0].strip(), int(entry[1]), float(entry[2])
    return "", 0, 0


def calculate_std_dev(data_list):
    mean = calculate_mean(data_list)
    sqd_diff = 0
    for val in data_list:
        sqd_diff += (val - mean) ** 2

    return (sqd_diff / len(data_list)) ** .5


def days_outside_of_range(adj_closes, mean, std_dev_range):
    days_ago = 0
    for val in reversed(adj_closes):
        if mean - std_dev_range < val:
            return days_ago
        days_ago += 1
    return len(adj_closes)


def get_perc_diff(val1, val2):
    return int((abs(val1 - val2) / (val1 + val2) / 2) * 100)


def print_alert(stock):
    print('Buy alert for {}'.format(stock.ticker))
    print('Price: {:.2f}, Mean: {:.2f}'.format(stock.price, stock.mean))
    print('Price + std_dev: {:.2f}, Difference {}%'.format(stock.price + stock.std_dev, stock.margin))
    print('Buy {} shares'.format(int(ORDER_CAP / stock.price)))
    print()


def analyze_stock(stock):
    retry = 0
    price = -1
    while retry < STOCK_RETRY:
        try:
            stock_data = get_data(
                stock,
                start_date=(datetime.datetime.today() - datetime.timedelta(weeks=52)).strftime('%m/%d/%Y'),
                end_date=datetime.datetime.today().strftime('%m/%d/%Y')
            )
            price = get_live_price(stock)
            break
        except:
            retry += 1
            if retry == STOCK_RETRY:
                return -1,0,0

    adj_closes = stock_data.loc[:, 'adjclose'].tolist()
    mean = calculate_mean(adj_closes)
    std_dev = calculate_std_dev(adj_closes)
    return price, mean, std_dev


def get_time_str(seconds):
    hours = str(int(seconds / 3600)).zfill(1)
    minutes = '{}'.format(int(seconds % 3600 / 60)).zfill(2)
    seconds = str(seconds % 60).zfill(2)
    return '{}:{}:{}'.format(hours, minutes, seconds)


def analyze_market(stock_list, bought_list):
    unfound_stocks = []
    stocks_to_buy = []
    i = 0
    num_stocks = 0
    start_time = datetime.datetime.now()
    stock_list_len = len(stock_list)

    print("Started analysis at", start_time)
    for stock in stock_list:
        if stock not in bought_list:
            stock_strip = stock[0].strip()
            price, mean, std_dev = analyze_stock(stock_strip)
            if price == -1:
                unfound_stocks.append(stock)
                continue

            if price < mean - std_dev * BUY_MULTIPLIER:
                stocks_to_buy.append(Stock(stock_strip, price, mean, std_dev, get_perc_diff(price + std_dev, mean)))
                num_stocks += 1

        i += 1
        perc_done = (i / stock_list_len) * 100
        perc_done_str = '{:.2f}%'.format(perc_done)

        seconds_elapsed = int((datetime.datetime.now() - start_time).total_seconds())
        time_elapsed_str = get_time_str(seconds_elapsed)

        total_run_time = int(100 * seconds_elapsed / perc_done)
        total_run_time_str = get_time_str(total_run_time)

        seconds_left = total_run_time - seconds_elapsed
        time_left_str = get_time_str(seconds_left)

        sys.stdout.write("\r{} Running Time: {} Finish Time: {} Time left: {} Stocks Analyzed: {}/{} Stocks found: {}"
                         .format(perc_done_str, time_elapsed_str, total_run_time_str, time_left_str, i, stock_list_len, num_stocks))
    print()

    stocks_to_buy.sort(key=lambda x: x.margin, reverse=True)
    for stock in stocks_to_buy:
        print_alert(stock)

    if unfound_stocks:
        print("No data for following stocks")
        for stock in unfound_stocks:
            print("{}".format(stock))


def analyze_portfolio(bought_list):
    for row in bought_list:
        stock, shares, bought_at = get_bought_info(row[0], bought_list)
        price, mean, std_dev = analyze_stock(stock)
        if price == -1:
            continue

        gain_loss_per_share = price - bought_at
        today = datetime.datetime.today()

        print(stock)
        print('Bought {} shares at {}. Margin: {:.2f}'.format(shares, bought_at, gain_loss_per_share))
        print('Lost/gained {:.2f} '.format(gain_loss_per_share * shares))
        if price > mean - std_dev * SELL_MULTIPLIER:
            print_alert('Sell', price, mean, stock, std_dev)
        else:
            print('Price: {:.2f}, Mean: {:.2f}, Difference {}%'.format(price, mean, get_perc_diff(mean, price)))
            print('Sell at {:.2f}'.format(mean - std_dev * SELL_MULTIPLIER))
        print('\n')


bought_list = list(csv.reader(open('bought.txt')))
stock_list = list(csv.reader(open('stocks.txt')))

print('Portfolio Analysis')
analyze_portfolio(bought_list)

print('Stock analysis')
analyze_market(stock_list, bought_list)
print('Done')







