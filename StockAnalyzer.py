from yahoo_fin.stock_info import *
import datetime
import csv

STD_DEV_MULTIPLIER = 2


def calculate_mean(data_list):
    sum = 0
    for val in data_list:
        sum += val
    return sum / len(data_list)


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
        if val > mean + std_dev_range or val < mean - std_dev_range:
            return days_ago
        days_ago += 1
    return len(adj_closes)


def get_perc_diff(val1, val2):
    return int((abs(val1 - val2) / (val1 + val2) / 2) * 100)


def print_alert(buy_sell, price, mean, stock_strip, days_ago):
    perc_diff = get_perc_diff(price, mean)
    print('{} alert for {}'.format(buy_sell, stock_strip))
    print('Price: {:.2f}, Mean: {:.2f}, Difference {}%'.format(price, mean, perc_diff))
    print('Last within range {} days ago\n'.format(days_ago))


def analyze_stock(stock):
    stock_data = get_data(
        stock,
        start_date=(datetime.datetime.today() - datetime.timedelta(weeks=52)).strftime('%m/%d/%Y'),
        end_date=datetime.datetime.today().strftime('%m/%d/%Y')
    )
    adj_closes = stock_data.loc[:, 'adjclose'].tolist()
    mean = calculate_mean(adj_closes)
    std_dev_range = calculate_std_dev(adj_closes) * STD_DEV_MULTIPLIER
    price = adj_closes[-1]
    days_ago = days_outside_of_range(adj_closes, mean, std_dev_range)
    return price, mean, std_dev_range, days_ago


def analyze_market(stock_list, bought_list):
    for stock in stock_list:
        stock_strip = stock[0].strip()
        price, mean, std_dev_range, days_ago = analyze_stock(stock_strip)

        if price < mean - std_dev_range:
            print_alert('Buy', price, mean, stock_strip, days_ago)
            stock, shares, bought_at, date = get_bought_info(stock_strip, bought_list)
            if stock:
                print('Bought {} shares on {} at {}\n'.format(shares, date, bought_at))

        if price > mean + std_dev_range:
            stock, shares, bought_at, date = get_bought_info(stock_strip, bought_list)
            if stock:
                print_alert('Sell', price, mean, stock_strip, days_ago)
                print('Bought {} shares on {} at {}'.format(shares, date, bought_at.strftime('%Y-%m-%d')))


def analyze_portfolio(bought_list):
    for row in bought_list:
        stock, shares, bought_at, date = get_bought_info(row[0], bought_list)
        price, mean, std_dev_range, days_ago = analyze_stock(stock)
        if price == -1:
            continue

        gain_loss_per_share = bought_at - price
        today = datetime.datetime.today()
        print(stock)
        print('Margin: {:.2f}'.format(gain_loss_per_share))
        print('Lost/gained {:.2f} over {} days'.format(gain_loss_per_share * int(row[1]),
                                                   abs((today - date).days)))
        print('Price: {:.2f}, Mean: {:.2f}, Difference {}%'.format(price, mean, get_perc_diff(mean, price)))
        print('Last within range {} days ago\n'.format(days_ago))


bought_list = list(csv.reader(open('bought.txt')))
stock_list = list(csv.reader(open('stocks.txt')))

analyze_portfolio(bought_list)
analyze_market(stock_list, bought_list)
print('Done')







