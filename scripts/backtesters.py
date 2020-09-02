"""
This file holds the classes that act as backtesters. These classes hold
functions that help tabulate data and determine when to buy/sell/hold, as
well as relevant variables that hold historical data of the symbol, as well as
the relevant actions taken while trading.
Lastly, this file holds helper functions that pertain to finding or organizing
backtesters for further use.
"""
import finlib
import pandas as pd
import numpy as np
import sys


# Examples of more investment strategies to try:
# https://www.macroaxis.com/invest/Momentum-Indicators/Absolute-Price-Oscillator/GOOG


class Backtester:
    """
    This class is inherited by all backtesters below. It holds variables that
    every backtester uses, as well as functions that every backtester uses.
    Some of these variables/functions are not used in this parent class; they
    are instead kept as a way to document their exact purpose in a central
    location.
    """
    def __init__(self, cash):
        """
        Initialize the class variables
        :param cash: The amount of money available at the beginning with
        which to invest.
        """
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
        """
        Updates price_update information into hist_datadict
        :param price_update: The day's stock information; a row from a dataframe
        :return: Nothing.
        """
        for key in self.hist_data_dict:
            self.hist_data_dict[key].append(price_update[key])

    def create_dataframe(self):
        """
        Converts the dictionary hist_data_dict into a dataframe.
        The information is saved as a dict initially in order to make these
        backtesters run faster. If they were instead appended onto a dataframe
        each day, the runtime would be *much* slower.
        :return: Nothing.
        """
        self.historical_data = pd.DataFrame.from_dict(data=self.hist_data_dict)

    def build_model(self, price_update):
        """
        This is where the model, if needed to be built, is made.
        Once made, it could either:
        1) update repeatedly (slower)
        2) never update again (faster, but possibly would become outdated)
        If doing an ML model, you'd use the fit(X, Y) command.
        :param price_update: The day's stock information; a row from a dataframe
        :return: Nothing.
        """
        pass

    def on_market_data_received(self, price_update):
        """
        This is where you send data when it is received.
        It can do the following:
        1) Send data to build_model if the model hasn't been built, or if
        you want to continuously update the model
        2) (More importantly) it should return an action (e.g. buy,
        sell, hold) based off of the model that you use.
        If doing an ML model, you'd use the predict() command.
        :param price_update: The day's stock information; a row from a dataframe
        :return: Nothing in this function, but usually a string: either
        'buy', 'sell', or 'hold'.
        """
        pass

    def buy_sell_or_hold(self, price_update, action):
        """
        This is where you send the price information, as well as the action,
        to complete whatever action the model tells you to do.
        This function can do the following:
        1) Fully buy or sell positions in a stock
        2) Not buy or sell a position in a stock if you don't have the
        required liquidity
        3) At the end, methods for the backtester's class should be updated
        to help keep the data on your position up to date.
        :param price_update: The day's stock information; a row from a dataframe
        :param action: 'buy', 'sell', or 'hold': Usually obtained from the
        function on_market_data_received()
        :return: Nothing.
        """
        pass


# Hold backtester
class Hodl(Backtester):
    """
    A backtester who's job is to buy as much of a stock as possible at the
    very beginning and do nothing else except keep relevant data tabulated.
    """
    def __init__(self, cash):
        """
        Initialize the class variables
        :param cash: The amount of money available at the beginning with
        which to invest.
        """
        self.name = 'HODL'
        super().__init__(cash)

    def build_model(self, price_update):
        """
        Where the backtester's model is built. There is no real model when we
        are just holding, so we just make sure to update our price and
        keep going.
        :param price_update: The day's stock information; a row from a dataframe
        :return: Nothing
        """
        self.update_hist_dict(price_update)
        pass

    def on_market_data_received(self, price_update):
        """
        This is where we figure out whether we want to buy, sell, or hold.
        We buy if it is the first day of trading for this backtester, and
        otherwise we hold.
        :param price_update: The day's stock information; a row from a dataframe
        :return: A string: either 'buy' or 'hold'.
        """
        self.market_data_count += 1
        self.build_model(price_update)

        if self.market_data_count == 1:
            # Only buy if we're just at the beginning
            return 'buy'
        else:
            return 'hold'

    def buy_sell_or_hold(self, price_update, action):
        """
        Here is where we compute the results of our actions when buying,
        selling, or holding, as well as update historical information.
        :param price_update: The day's stock information; a row from a dataframe
        :param action: A string, 'buy', 'sell', or 'hold'.
        :return: Nothing.
        """
        if action == 'buy':
            self.position += self.cash / price_update['Adj Close']
            self.cash = 0

        if action == 'sell':
            sys.exit("Tried to sell while holding")
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
    """
    This backtester is a Simple Moving Average (SMA) indicator. When the
    average adjusted price for the shorter period becomes larger than the
    average adjusted price for the longer period, we should buy and proceed
    to hold our position. When that average price for the shorter period
    becomes smaller than that average price for the longer period, we should
    sell our holdings and hold until it flips again.
    """
    def __init__(self, cash, short_period, long_period):
        """
        Initialize the class variables
        :param cash: The amount of money available at the beginning with which
        to invest.
        :param short_period: The length of the shorter moving average.
        :param long_period: The length of the longer moving average.
        """
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
        """
        Where we build our model; this has to happen every day as we need to
        calculate the new price averages for both moving averages.
        :param price_update: The day's stock information; a row from a dataframe
        :return: Nothing.
        """
        if len(self.short_window) == self.short_period:
            self.short_window.pop(0)  # Get rid of old information
        if len(self.long_window) == self.long_period:
            self.long_window.pop(0)  # Get rid of old information

        self.short_window.append(price_update['Adj Close'])
        self.long_window.append(price_update['Adj Close'])

        self.short_avg = np.mean(self.short_window)
        self.long_avg = np.mean(self.long_window)

    def on_market_data_received(self, price_update):
        """
        Where we figure out whether we want to buy, sell, or hold.
        :param price_update: The day's stock information; a row from a dataframe
        :return: A string: Either 'buy', 'sell', or 'hold'.
        """
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
        """
        Where we figure out what should happen after we've decided whether
        to buy, sell, or hold.
        :param price_update: The day's stock information; a row from a dataframe
        :param action: A string: Either 'buy', 'sell', or 'hold'.
        :return: Nothing
        """
        if action == 'buy':
            # In this model, we're just gonna yolo and use all of our cash
            # into buying the stock when we get the signal.
            # Here we buy as many positions of the stock as we can:
            self.position = np.floor(self.cash / price_update['Adj Close'])
            self.cash -= self.position * price_update['Adj Close']
        elif action == 'sell':
            # In this model, when we get a sell action we just sell all of our
            # position inside of the stock.
            self.cash += self.position * price_update['Adj Close']
            self.position = 0

        # Regular updates
        self.holdings = self.position * price_update['Adj Close']
        self.total = self.holdings + self.cash
        self.list_position.append(self.position)
        self.list_cash.append(self.cash)
        self.list_holdings.append(self.holdings)
        self.list_total.append(self.total)


class MACD(Backtester):
    """
    This backtester is a Moving Average Convergence Divergence (MACD) indicator,
    also known as an Exponential Moving Average indicator. It is similar to the
    SMA above, with one small change: instead of weighing each period the same
    for the window averages, it weighs more recent information higher than less
    recent info. As such, it should be more responsive to drastic price
    increases and (hopefully) catch wind of upticks or downticks sooner.
    """
    def __init__(self, cash, short_period, long_period):
        """
        Initialize the class variables
        :param cash: The amount of money available at the beginning with which
        to invest.
        :param short_period: The length of the shorter moving average.
        :param long_period: The length of the longer moving average.
        """
        # Necessary info
        self.name = 'MACD (%d, %d)' % (short_period, long_period)
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
        """
        Where we build the model that helps us determine whether to buy, sell,
        or hold. This needs to be updated daily as the moving averages change
        every day.
        :param price_update: The day's stock information; a row from a dataframe
        :return: Nothing
        """
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
        """
        WWhere we figure out whether to buy, sell, or hold.
        :param price_update: The day's stock information; a row from a dataframe
        :return: A string: Either 'buy', 'sell', or 'hold'.
        """
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
        """
        Where we figure out what to do once we've decided to buy, sell, or hold.
        :param price_update: The day's stock information; a row from a dataframe
        :param action: A string: Either 'buy', 'sell', or 'hold'.
        :return: Nothing.
        """
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

        # Regular updates
        self.holdings = self.position * price_update['Adj Close']
        self.total = self.holdings + self.cash
        self.list_position.append(self.position)
        self.list_cash.append(self.cash)
        self.list_holdings.append(self.holdings)
        self.list_total.append(self.total)


def backtesters(cash):
    """
    Returns initialized classes of backtesters that are 1) available/written,
    and 2) are generally useful to explore when trying to invest.
    Note: The changing of backtesters available to the investment strategy
    should happen here. This will DRASTICALLY change the average return of
    the portfolio.
    Second note: SMA is sometimes a valid backtester to use, but it seems like
    using MACD would be better for now because it takes advantage of weighing
    the most recent stock prices higher than older stock prices.
    :param cash: The amount of starting capital assumed for each backtester.
    :return: A list of initialized backtesters.
    """
    list_of_backtesters = [MACD(cash, 12, 26), Hodl(cash)]
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
    """
    This function organizes the dataframe historical_data present in each
    backtester class. This organization is not mandatory, but can sometimes
    help with computations, so it is left here in case.
    :param bt: The initialized backtester that has already figured out when to
    buy, sell, hold, etc.
    :return: Modifies the backtester in place.
    """
    bt.historical_data.set_index('Date', inplace=True)  # Change index to date
    bt.historical_data['Total'] = bt.list_total  # Organize total earnings
    finlib.excess_returns(bt.historical_data, risk_free_rate=0.05/252,
                          column_name='Total')  # Get excess returns
