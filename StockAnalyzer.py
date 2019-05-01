from yahoo_fin.stock_info import *
import datetime
import csv

BUY_MULTIPLIER = 1.7
SELL_MULTIPLIER = 1


def calculate_mean(data_list):
    sum = 0
    weight = 0
    for x in range(len(data_list) + 1):
        weight += x

    i = 1;
    for val in data_list:
        sum += val * i / weight
        i += 1
    return sum


def get_bought_info(stock, bought_list):
    for entry in bought_list:
        if entry[0] == stock:
            return entry[0].strip(), int(entry[1]), float(entry[2]), datetime.datetime.strptime(entry[3], "%Y-%m-%d")
    return "", 0, 0, datetime.datetime.today()


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


def print_alert(buy_sell, price, mean, stock_strip, std_dev):
    print('{} alert for {}'.format(buy_sell, stock_strip))
    print('Price: {:.2f}, Mean: {:.2f}, Difference {}%'.format(price, mean, get_perc_diff(price, mean)))
    print('Price + std_dev: {:.2f}, Difference {}%'.format(price + std_dev, get_perc_diff(price + std_dev, mean)))


def analyze_stock(stock):
    stock_data = get_data(
        stock,
        start_date=(datetime.datetime.today() - datetime.timedelta(weeks=52)).strftime('%m/%d/%Y'),
        end_date=datetime.datetime.today().strftime('%m/%d/%Y')
    )
    adj_closes = stock_data.loc[:, 'adjclose'].tolist()
    mean = calculate_mean(adj_closes)
    std_dev = calculate_std_dev(adj_closes)
    price = get_live_price(stock)
    return price, mean, std_dev


def analyze_market(stock_list, bought_list):
    for stock in stock_list:
        stock_strip = stock[0].strip()
        price, mean, std_dev = analyze_stock(stock_strip)

        if price < mean - std_dev * BUY_MULTIPLIER:
            stock, shares, bought_at, date = get_bought_info(stock_strip, bought_list)
            if not stock:
                print_alert('Buy', price, mean, stock_strip, std_dev)


def analyze_portfolio(bought_list):
    for row in bought_list:
        stock, shares, bought_at, date = get_bought_info(row[0], bought_list)
        price, mean, std_dev = analyze_stock(stock)
        if price == -1:
            continue

        gain_loss_per_share = price - bought_at
        today = datetime.datetime.today()

        print(stock)
        print('Bought {} shares on {} at {}. Margin: {:.2f}'.format(shares, date, bought_at, gain_loss_per_share))
        print('Lost/gained {:.2f} over {} days'.format(gain_loss_per_share * shares,
                                                       abs((today - date).days)))
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







