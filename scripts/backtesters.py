import pandas as pd
import numpy as np
import sys
import finlib


# Examples of more investment strategies to try:
# https://www.macroaxis.com/invest/Momentum-Indicators/Absolute-Price-Oscillator/GOOG


class Backtester:
    def __init__(self, cash):
        # Information that is used in each backtester
        self.list_position = []  # List of positions held at each date
        self.list_cash = []  # List of cash owned at each date
        self.list_holdings = []  # position * price at each date
        self.list_total = []  # holdings + cash at each date

        self.cash = cash  # Hold variable of current liquidity
        self.total = cash  # Hold variable of current total net worth
        self.position = 0  # Hold variable of current position
        self.holdings = 0  # Hold variable of current holdings
        self.market_data_count = 0  # How much market info you have

        # In case you want to hold all of the information, you can append
        # it to this dataframe.
        self.historical_data = None

        # Holds temp data for dataframe; by creating the dataframe from a dict
        # instead of appending each time, we can greatly speed up the
        # backtesting process.
        self.hist_data_dict = {'Date': [], 'Adj Close': [], 'High': [],
                               'Low': [], 'Open': [], 'Close': [],
                               'Volume': []}

    def update_hist_dict(self, price_update):
        for key in self.hist_data_dict:
            self.hist_data_dict[key].append(price_update[key])

    def create_dataframe(self):
        self.historical_data = pd.DataFrame.from_dict(data=self.hist_data_dict)

    def build_model(self, price_update):
        # This is where the model, if needed to be built, is made.
        # Once made, it could either:
        # 1) update repeatedly (slower)
        # 2) never update again (faster, but possibly would become outdated)
        # If doing an ML model, you'd use the fit(X, Y) command.
        pass

    def on_market_data_received(self, price_update):
        # This is where you send data when it is received.
        # It can do the following:
        # 1) Send data to build_model if the model hasn't been built, or if
        # you want to continuously update the model
        # 2) (More importantly) it should return an action (e.g. buy,
        # sell, hold) based off of the model that you use.
        # If doing an ML model, you'd use the predict() command.
        pass

    def buy_sell_or_hold(self, price_update, action):
        # This is where you send the price information, as well as the action,
        # to complete whateveraction the model tells you to do.
        # This function can do the following:
        # 1) Fully buy or sell positions in a stock
        # 2) Not buy or sell a position in a stock if you don't have the
        # required liquidity
        # 3) At the end, methods for the backtester's class should be updated
        # to help keep the data on your position up to date.
        pass


# Hold backtester
class Hodl(Backtester):
    def __init__(self, cash):
        self.name = 'HODL'
        super().__init__(cash)

    def build_model(self, price_update):
        # No model when we're just holding
        self.update_hist_dict(price_update)
        # self.historical_data = self.historical_data.append(price_update,
        #                                                    ignore_index=True)
        pass

    def on_market_data_received(self, price_update):
        self.market_data_count += 1
        self.build_model(price_update)

        if self.market_data_count == 1:
            # Only buy if we're just at the beginning
            return 'buy'
        else:
            return 'hold'

    def buy_sell_or_hold(self, price_update, action):
        if action == 'buy':
            self.position += self.cash / price_update['Adj Close']
            self.cash = 0

        if action == 'sell':
            # Not possible, because we're hodl.
            pass

        if action == 'hold':
            # You specifically do nothing when you hold.
            pass

        # Regular updates
        self.holdings = self.position * price_update['Adj Close']
        self.total = (self.holdings + self.cash)
        self.list_position.append(self.position)
        self.list_cash.append(self.cash)
        self.list_holdings.append(self.holdings)
        self.list_total.append(self.holdings + self.cash)


# Simple Moving Average backtester; not currently used.
class SMA(Backtester):
    def __init__(self, cash, short_period, long_period):
        # Necessary info
        self.name = 'Simple Moving Avg (%d, %d)' % (short_period, long_period)
        super().__init__(cash)

        # Additional information specifically for this backtester
        self.long_signal = False  # A function of the rolling windows
        self.prev_price = None  # Helps with the rolling average
        self.short_period = short_period
        self.long_period = long_period
        self.short_window = []
        self.long_window = []
        self.short_avg = None
        self.long_avg = None

    def build_model(self, price_update):
        if len(self.short_window) == self.short_period:
            self.short_window.pop(0)  # Get rid of old information
        if len(self.long_window) == self.long_period:
            self.long_window.pop(0)  # Get rid of old information

        self.short_window.append(price_update['Adj Close'])
        self.long_window.append(price_update['Adj Close'])

        self.short_avg = np.mean(self.short_window)
        self.long_avg = np.mean(self.long_window)

    def on_market_data_received(self, price_update):
        self.market_data_count += 1
        self.build_model(price_update)

        # Should only choose to buy or sell once we have enough info
        if self.market_data_count < self.long_period:
            return 'hold'
        else:
            if self.long_signal and (self.short_avg > self.long_avg):
                return 'hold'
            elif self.long_signal and (self.short_avg < self.long_avg):
                self.long_signal = False
                return 'sell'
            elif not self.long_signal and (self.short_avg > self.long_avg):
                self.long_signal = True
                return 'buy'
            elif not self.long_signal and (self.short_avg < self.long_avg):
                return 'hold'

    def buy_sell_or_hold(self, price_update, action):
        if action == 'buy':
            # In this model, we're just gonna yolo and use all of our cash
            # into buying the stock.
            # Here we buy as many positions of the stock as we can:
            self.position = np.floor(self.cash / price_update['Adj Close'])
            self.cash -= self.position * price_update['Adj Close']
        elif action == 'sell':
            # In this model, when we get a sell action we just sell all of our
            # position inside of the stock.
            self.cash += self.position * price_update['Adj Close']
            self.position = 0

        self.holdings = self.position * price_update['Adj Close']
        self.total = self.holdings + self.cash
        # print('%s total=%d, holding=%d, cash=%d' %
        #       (str(price_update['Date']),self.total, self.holdings, self.cash))

        self.list_position.append(self.position)
        self.list_cash.append(self.cash)
        self.list_holdings.append(self.holdings)
        self.list_total.append(self.total)


class MACD(Backtester):
    def __init__(self, cash, short_period, long_period):
        # Necessary info
        self.name = 'MACD (%d, %d)' % \
                    (short_period, long_period)
        super().__init__(cash)

        # Additional information specifically for this backtester
        self.long_signal = False  # A function of the rolling windows
        self.short_period = short_period
        self.long_period = long_period
        self.short_window = []  # Holds closing price from past days
        self.long_window = []  # Holds closing price from past days
        self.short_ema = None  # Current day's short ema
        self.long_ema = None  # Current day's long ema
        self.prev_short_ema = None  # Previous day's short ema
        self.prev_long_ema = None  # Previous day's long ema

    def build_model(self, price_update):
        # self.historical_data = self.historical_data.append(price_update,
        #                                                    ignore_index=True)
        self.update_hist_dict(price_update)

        if len(self.short_window) == self.short_period:
            self.short_window.pop(0)  # Get rid of old information
        if len(self.long_window) == self.long_period:
            self.long_window.pop(0)  # Get rid of old information

        # Updating windows for today's information
        self.short_window.append(price_update['Adj Close'])
        self.long_window.append(price_update['Adj Close'])

        # Updating previous emas.
        self.prev_short_ema = self.short_ema
        self.prev_long_ema = self.long_ema

        # The first ema on the first day is equal to the closing price
        # If we didn't do this, we'd try to subtract a None value, which
        # obviously doesn't work.
        if self.prev_short_ema is None and self.prev_long_ema is None:
            self.prev_short_ema = price_update['Adj Close']
            self.prev_long_ema = price_update['Adj Close']

        # Calculating multiplier
        short_mult = 2 / (len(self.short_window) + 1)
        long_mult = 2 / (len(self.long_window) + 1)

        # Calculating current EMAs
        self.short_ema = ((price_update['Adj Close'] - self.prev_short_ema) *
                          short_mult) + self.prev_short_ema
        self.long_ema = ((price_update['Adj Close'] - self.prev_long_ema) *
                         long_mult) + self.prev_long_ema

    def on_market_data_received(self, price_update):
        self.market_data_count += 1
        self.build_model(price_update)

        # Should only choose to buy or sell once we have enough info
        if self.market_data_count <= self.long_period:
            return 'hold'
        else:
            if self.long_signal and (self.short_ema > self.long_ema):
                return 'hold'
            elif self.long_signal and (self.short_ema < self.long_ema):
                self.long_signal = False
                return 'sell'
            elif not self.long_signal and (self.short_ema > self.long_ema):
                self.long_signal = True
                return 'buy'
            elif not self.long_signal and (self.short_ema < self.long_ema):
                return 'hold'

    def buy_sell_or_hold(self, price_update, action):
        if action == 'buy':
            # In this model, we're just gonna yolo and use all of our cash
            # into buying the stock.
            # Here we buy as many positions of the stock as we can:
            self.position = np.floor(self.cash / price_update['Adj Close'])
            self.cash -= self.position * price_update['Adj Close']
        elif action == 'sell':
            # In this model, when we get a sell action we just sell all of our
            # position inside of the stock.
            self.cash += self.position * price_update['Adj Close']
            self.position = 0

        self.holdings = self.position * price_update['Adj Close']
        self.total = self.holdings + self.cash
        # print('%s total=%d, holding=%d, cash=%d' %
        #       (str(price_update['Date']),self.total, self.holdings, self.cash))

        self.list_position.append(self.position)
        self.list_cash.append(self.cash)
        self.list_holdings.append(self.holdings)
        self.list_total.append(self.total)


def backtesters(cash):
    """
    Returns initialized classes of backtesters that are 1) available/written,
    and 2) are generally useful to explore when trying to invest.
    :param cash: The amount of starting capital assumed for each backtester.
    If not specified, then it is assumed to be 10k.
    :return: A list of initialized backtesters.
    """
    # Whenever new backtesters are made, this list needs to be chagned in order
    # to return all of the available backtesters.
    # list_of_backtesters = [Hodl(cash),
    #                        MACD(cash, 5, 50),
    #                        MACD(cash, 10, 50),
    #                        MACD(cash, 5, 75),
    #                        MACD(cash, 12, 26)]
    # list_of_backtesters = [Hodl(cash), MACD(cash, 12, 26)]
    list_of_backtesters = [MACD(cash, 12, 26), Hodl(cash)]
    # - RandomBackTester isn't included because it is a template backtester to
    # help write future backtesters.
    # - ForLoopBackTester (aka Naive Backtester) is just that: Naive, and not
    # a good backtester except by chance. Thus, it is not included, and is kept
    # in this code as a reference.
    # - SMA is sometimes a valid backtester to use, but it seems like using
    # MACD is generally better because it takes advantage of weighing
    # the most recent stock prices higher than older stock prices.

    return list_of_backtesters


def find_backtester(name, cash):
    """
    Returns initialized class of a backtester when just given a string of the
    backtesters name, instead of returning a list of all available backtesters.
    :param name: name of wanted backtester. A string.
    :param cash: cash that is used when initializing this backtester. Int.
    :return: The initialized backtester, or None if that backtester doesn't
    exist.
    """
    list_of_backtesters = backtesters(cash)
    for backtester in list_of_backtesters:
        if backtester.name == name:
            return backtester
    sys.exit("Couldn't find backtester of name: " + name)


def organize_backtester(bt):
    bt.historical_data.set_index('Date', inplace=True)  # Change index to date
    bt.historical_data['Total'] = bt.list_total  # Organize total earnings
    finlib.excess_returns(bt.historical_data, risk_free_rate=0.05/252,
                          column_name='Total')




