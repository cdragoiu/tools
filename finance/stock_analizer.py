#!/usr/local/bin/python3

from argparse import ArgumentParser
import datetime  # date and time manipulations
from matplotlib import pyplot
import numpy as np
import re  # regular expression operations
import requests  # HTTP requests
from termcolor import colored  # colored terminal output

def get_cookie_crumb(url='https://finance.yahoo.com/quote/SPY/history'):
    '''
    Return site cookie and crumb needed to access stock data.
    Args:
        url: site providing historical stock data (optional)
    '''

    res = requests.get(url)
    cookie = res.cookies['B']
    crumb = None
    pattern = re.compile('.*"CrumbStore":\{"crumb":"(?P<crumb>[^"]+)"\}')
    for line in res.text.splitlines():
        m = pattern.match(line)
        if m is not None:
            crumb = m.groupdict()['crumb']
            return cookie, crumb

def get_stock_data(stock, days, cookie, crumb,
                   url='https://query1.finance.yahoo.com/v7/finance/download/'):
    '''
    Return historic stock prices covering N days in the past from today.
    Args:
        stock:  stock symbol
        days:   number of days in the past from today
        cookie: site cookie needed to access stock data
        crumb:  site crumb needed to access stock data
        url:    site providing historical stock data (optional)
    '''

    time_past = (datetime.date.today() - datetime.timedelta(days=days)).strftime('%s')
    time_curr = datetime.date.today().strftime('%s')
    interval = '1d' if days < 367 else '1wk'
    params = {'symbol': stock,
              'period1': time_past,
              'period2': time_curr,
              'interval': interval,
              'crumb': crumb}
    res = requests.get(url, params=params, cookies={'B' : cookie})
    return res.text

class StockAnalizer:
    '''
    Provides several tools to analyze the historic prices of a given stock. On top of the stock
    price, several EMAs (Exponential Moving Averages) can also be displayed. The stock trend can be
    added as an overlay display.
    '''

    def __init__(self):
        self.date = []
        self.price = []
        self.ema = {}
        self.trend = []

    def process_stock_data(self, history):
        '''
        Process historic stock prices and store them internally for future manipulations.
        Args:
            history: historic stock prices in a text format
        '''

        date_idx = None
        price_idx = None
        process_header = True
        for line in history.splitlines():
            data = line.split(',')
            if process_header:
                try:
                    date_idx = data.index('Date')
                except:
                    print('\ndate information not available\n')
                    return
                try:
                    price_idx = data.index('Close')
                except:
                    print('\nprice information not available\n')
                    return
                process_header = False
                continue
            if data[price_idx] == 'null':
                continue
            dt = data[date_idx].split('-')
            self.date.append(dt[1] + '/' + dt[2] + '/' + dt[0][2:])  # store date as MM/DD/YY
            self.price.append(float(data[price_idx]))

    def compute_ema_data(self, days):
        '''
        Compute and store internally EMAs based on given number of days.
        Args:
            days: number of days to use when averaging
        '''

        # return if no stock data
        if len(self.date) == 0:
            print('\ncompute_ema_data: skipping...no data available\n')
            return

        # compute EMAs
        self.ema[days] = [self.price[0]]
        w = 2.0 / (days + 1)  # stock price weight
        for i in range(1, len(self.price)):
            ema = self.price[i] * w + self.ema[days][-1] * (1 - w)
            self.ema[days].append(ema)

    def compute_trend_data(self, ema_key, stride):
        '''
        Compute and store internally the trend of the stock over time. The trend is calculated
        based on previously computed EMA and the given stride.
        Args:
            ema_key: specifies what EMA to use when computing the trend
            stride:  determines what reference value to use when computing the trend
        '''

        # return if EMA key not found
        if ema_key not in self.ema.keys():
            print('\ncompute_trend_data: skipping...selected EMA not available\n')
            return

        # compute the trend
        for i in range(len(self.date)):
            ref = self.ema[ema_key][max(0, i - stride)]
            dif = 100.0 * (self.ema[ema_key][i] - ref) / ref  # as percentage
            self.trend.append(dif)

    def plot_data(self, stock, period, path):
        '''
        Show on a plot the historic stock price, the computed EMAs and the trend if available.
        Args:
            stock:  stock symbol
            period: some text indicating the time period that is displayed
            path:   save plot if path is provided
        '''

        # return if no stock data
        if len(self.date) == 0:
            print('\nplot_data: skipping...no data available\n')
            return

        # set up the plot
        fig = pyplot.figure(1, figsize=(10, 4))
        fig.subplots_adjust(left=0.07, bottom=0.1, right=0.93, top=0.9)
        plt_trend = fig.subplots()
        plt_trend.set_ylabel('Trend (%)')
        plt_trend.yaxis.label.set_color('green')
        plt_trend.tick_params(axis='y', colors='green')
        plt_price = plt_trend.twinx()
        plt_price.set_ylabel('Price ($)')

        # plot stock price
        if len(self.date) != 0:
            plt_price.plot(self.date, self.price, 'black', linewidth=1.5)
            plt_price.yaxis.set_label_coords(-0.07, 0.5)
            plt_price.yaxis.tick_left()

        # plot EMAs
        ema_clr = ['blue', 'red', 'purple', 'orange']
        for i, key in enumerate(self.ema.keys()):
            plt_price.plot(self.date, self.ema[key], ema_clr[i % len(ema_clr)], linewidth=1,
                           label='EMA '+str(key))

        # plot trend
        if len(self.trend) != 0:
            plt_trend.plot(self.date, self.trend, 'green', linewidth=1, linestyle='dotted')
            plt_trend.axhline(y=0.0, color='grey', linewidth=1, linestyle='dotted')
            plt_trend.yaxis.set_label_coords(1.07, 0.5)
            plt_trend.yaxis.tick_right()

        # set up labels on x-axis
        nx = 8  # number of labels on x-axis
        pyplot.xticks([int(1.0 * i * (len(self.date) - 1) / (nx - 1)) for i in range(nx)])

        # set up title
        price_now = self.price[-1]
        price_old = self.price[0]
        pyplot.suptitle(
            stock.upper() +
            '   •   ${:.2f}'.format(price_now) +
            '   •   {:.2f}% ('.format(100.0 * (price_now - price_old) / price_old) +
            period.upper() + ')'
        )

        plt_price.legend(frameon=False)
        if path is not None:
            pyplot.savefig(path + stock.lower() + '_' + period.lower(), dpi=100)
        pyplot.show()

def main():
    # set up command-line options
    parser = ArgumentParser(description='Display trends of the selected stock(s).', add_help=True)
    parser.add_argument('positional', metavar='stock', nargs='+', help='stock symbol(s)')
    group_time = parser.add_mutually_exclusive_group(required=True)
    group_time.add_argument('-w', '--week', metavar='time', type=int, help='time interval in weeks')
    group_time.add_argument('-m', '--month', metavar='time', type=int, help='time interval in months')
    group_time.add_argument('-y', '--year', metavar='time', type=int, help='time interval in years')
    group_extra = parser.add_mutually_exclusive_group()
    group_extra.add_argument('-c', '--correlation', action='store_true',
                             help='compute stock correlation(s) (at least two stocks must be given)')
    group_extra.add_argument('-s', '--save', metavar='path',
                             help='save stock trends as PNG files using given path')
    args = parser.parse_args()

    # parse arguments
    stocks = args.positional
    if args.week is not None:
        period = args.week * 7
        period_str = str(args.week) + 'W'
    elif args.month is not None:
        period = args.month * 30
        period_str = str(args.month) + 'M'
    elif args.year is not None:
        period = args.year * 365
        period_str = str(args.year) + 'Y'
    if args.correlation and len(stocks) < 2:
        print('\nat least two stocks must be given to compute correlation\n')
        exit()

    # get site handles
    while True:
        cookie, crumb = get_cookie_crumb()
        if '\\u002' not in crumb:
            break

    # process stocks
    stock_ana = {}
    for stock in stocks:
        history = get_stock_data(stock, period, cookie, crumb)
        if 'error' in history:
            print('\nunable to retrive data for ' + stock.upper() + '\n')
            continue
        stock_ana[stock] = StockAnalizer()
        stock_ana[stock].process_stock_data(history)

    # print correlation(s)
    if args.correlation:
        prices = []
        for stock, analzr in stock_ana.items():
            price_diff = np.diff(analzr.price)
            prices.append({'stock' : stock, 'diff' : price_diff,
                           'mean' : price_diff.mean(), 'std' : price_diff.std()})
        n = len(prices)
        for i in range(n):
            print()
            for j in range(n):
                if j == i:
                    continue
                corr = np.sum((prices[i]['diff'] - prices[i]['mean']) *
                              (prices[j]['diff'] - prices[j]['mean']))
                corr /= len(prices[i]['diff']) * prices[i]['std'] * prices[j]['std']
                color = 'green' if corr < 0.6 else 'white'
                color = 'magenta' if corr > 0.8 else color
                print(colored('{:>5} - {:<5} : {:+.2f}', color).format(
                      prices[i]['stock'].upper(), prices[j]['stock'].upper(), corr))
        print()
        exit()

    # display trends
    for stock, analzr in stock_ana.items():
        analzr.compute_ema_data(days=5)
        analzr.compute_ema_data(days=20)
        analzr.compute_trend_data(ema_key=20, stride=5)
        analzr.plot_data(stock, period_str, path=args.save)

if __name__ == '__main__':
    main()
