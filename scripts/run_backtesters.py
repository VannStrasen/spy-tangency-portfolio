import obtain_symbols
import finlib
import backtesters
import pandas as pd
import sys
import os
from pandas_datareader import data


class SymbolsHelper:
    """
    A class that holds important information for calculating misc. commands,
    or that holds information so that it doesn't need to be redownloaded and
    thus increasing function speeds.
    """
    def __init__(self):
        # This dictionary holds a dataframe of historical information for
        # each symbol that needs it. This dict looks like this:
        # {'symbol1': dataframe1, 'symbol2': dataframe2, ...}
        self.symbol_data_dict = {}

        # This dictionary holds the relevant backtesters that have last been
        # used for each symbol. This is in part necessary because it helps
        # the program realize what type of backtester (Hodl, MACD, SMA, etc)
        # the portfolio used before so that previously finalized backtesters
        # don't change. All of these backtesters are classess that are built
        # in the file backtesters.py. This dict looks like this:
        # {'symbol1': backtester1, 'symbol2': backtester2, ...}
        self.symbol_backtesters_dict = {}

        # This dictionary holds all industries used in the main portfolio, as
        # well as all symbols used in each industry. This dict looks like this:
        # {'industry1': ['sym1', 'sym2'...], 'industry2': ['sym3'...]...}
        self.obtained_symbols_dict = None


def run_backtester(backtester, symbol_data):
    """
    This function uses the data in symbol_data, as well as the buying/selling/
    holding conditions in backtester, to run through historical data on a symbol
    and calculate the performance of this backtester over the days of stock info
    in symbol_data.
    :param backtester: An initialized backtester class from backtesters.py
    :param symbol_data: A dataframe obtained from yahoo finance containing
    information on a stock's historical trade data
    :return: The backtester in the input stores all of the information, so this
    function does not need to return anything.
    """
    for i in range(len(symbol_data)):  # Read in symbol data
        # Daily information, consolidated into a dictionary.
        price_info = {'Date': symbol_data.index[i],
                      'Adj Close': float(symbol_data['Adj Close'][i]),
                      'High': float(symbol_data['High'][i]),
                      'Low': float(symbol_data['Low'][i]),
                      'Open': float(symbol_data['Open'][i]),
                      'Close': float(symbol_data['Close'][i]),
                      'Volume': float(symbol_data['Volume'][i])}

        # The action that the backtester decides to do, given the price
        # information. This can be 'buy', 'sell', or 'hold'.
        action = backtester.on_market_data_received(price_info)
        # Running this action back into the backtester to simulate market
        # actions.
        backtester.buy_sell_or_hold(price_info, action)

    # Create the dataframe that will hold all the symbol's and trading
    # data.
    backtester.create_dataframe()
    return


def examine_backtesters(symbol_data, cash, backtester_names=None):
    """
    This function initializes and runs (through the helper function
    run_backtester) one/multiple backtesters, and returns the backtester with
    the highest sharpe ratio.
    :param symbol_data: A dataframe obtained from yahoo finance containing
    information on a stock's historical trade data
    :param cash: Int; the amount of money that we can use inside one backtester
    :param backtester_names: A list of strings containing the names of
    backtesters that the programmer wants to initialize to test. If None,
    this function initializes a preset list of backtesters (see
    backtesters.backtesters(cash))
    :return: The backtester that obtained the higehst sharpe ratio over
    the symbol_data.
    """
    # First, we have to initialize all of the backtesters that we have.
    if backtester_names is not None:
        list_of_backtesters = []
        for name in backtester_names:
            list_of_backtesters.append(backtesters.find_backtester(name, cash))
    else:
        list_of_backtesters = backtesters.backtesters(cash)

    # Return the best backtester, where best = highest sharpe ratio
    res_backtester = None
    res_backtester_sharpe = None
    for backtester in list_of_backtesters:
        run_backtester(backtester, symbol_data)
        backtesters.organize_backtester(backtester)
        sharpe_ratio = finlib.tangency_summary(backtester.historical_data)
        if res_backtester_sharpe is None or \
                res_backtester_sharpe < sharpe_ratio:
            res_backtester = backtester
            res_backtester_sharpe = sharpe_ratio

    print("Backtester chosen:", res_backtester.name)
    return res_backtester


def run_tangency_portfolio(wts_tangency, cash, symb_help):
    """
    This function calculates the excess returns of a single-industry tangency
    portfolio by running previously chosen backtesters with updated cash
    allotments.
    :param wts_tangency: A pandas series that contains the respective weight
    for each symbol inside of an industry. The symbol's weight * cash =
    the amount of money allocated to that symbol.
    :param cash: Int; amount of money allocated across the entire industry, to be
    distributed in different weights to each symbol.
    :param symb_help: Initialized SymbolHelper class that contains information
    on the symbols being used + their backtesters.
    :return: tangency_res, a dataframe that holds net cash + holdings per day
    for the industry as a total, after weighing each symbol.
    """
    tangency_res = None  # A dataframe holding cash + holdings per day

    # Let's loop through all symbols in the tangency portfolio we found, run
    # their respective backtester, and append to tangency_res their cash +
    # holdings per day.
    for symbol, weight in wts_tangency.iteritems():
        allocation = cash * weight
        bt_name = symb_help.symbol_backtesters_dict[symbol].name
        bt = backtesters.find_backtester(bt_name, allocation)
        symbol_data = symb_help.symbol_backtesters_dict[symbol].historical_data
        run_backtester(bt, symbol_data)
        backtesters.organize_backtester(bt)

        if tangency_res is None:
            tangency_res = pd.DataFrame(data=bt.list_total,
                                        index=bt.historical_data.index,
                                        columns=['Total'])
        else:
            tangency_res['Total'] = tangency_res['Total'] + \
                                    bt.list_total

    # Calculating excess return
    finlib.excess_returns(tangency_res, risk_free_rate=0.05/252,
                          column_name='Total')

    return tangency_res


def run_final_tangency_portfolio(main_wts, industry_wts, cash, symb_help):
    """
    This function calculates the excess returns of a multi-industry tangency
    tangency portfolio by running previously chosen backtesters with updated
    cash allotments.
    :param main_wts: A pandas series that contains the respective weight for
    each industry inside of the main portfolio. The industry's weight * cash =
    the amount of money allocated to that industry
    :param industry_wts: A pandas series that contains the respective weight
    for each symbol inside of an industry. The symbol's weight * industry's cash
    = the amount of money allocated to that symbol.
    :param cash: Int; amount of money allocated across the entire portfolio, to
    be distributed in different weights to each industry, and further
    distributed in different weights to each symbol.
    :param symb_help: initialized SymbolHelper class that contains information
    on the symbols being used + their backtesters.
    :return: daily_total, a dataframe that holds net cash + holdings per day
    for the portfolio as a total, after weighing each industry and symbol.
    """
    print("\n\n*** Running backtest of main tangency portfolio to see its results")

    daily_total = None  # A dataframe holding cash + holdings per day

    # Let's loop through all industries in the tangency portfolio we found, run
    # the function 'run_tangency_portfolio on each industry, and append to
    # tangency_res each industry's cash + holdings per day.
    for industry, weight in main_wts.iteritems():
        industry_cash = cash * weight
        print("Running tangency portfolio for (" + industry + ") with $" +
              str(industry_cash))
        tangency_res = run_tangency_portfolio(industry_wts[industry],
                                              industry_cash, symb_help)

        if daily_total is None:
            daily_total = pd.DataFrame(data=tangency_res['Total'],
                                       index=tangency_res.index,
                                       columns=['Total'])
        else:
            daily_total['Total'] = daily_total['Total'] + tangency_res['Total']

    # Calculating excess return
    finlib.excess_returns(daily_total, risk_free_rate=0.05/252,
                          column_name='Total')

    # Summary statistics
    print("\nInitial investment in main tangency portfolio:", cash)
    print("Total profit:", round(daily_total.iloc[-1]['Total'] - cash, 2))
    print("Annualized sharpe ratio:",
          round(finlib.get_annualized_sharpe_ratio_df(daily_total), 3))

    return daily_total


def run_out_of_sample(main_wts, industry_wts, cash, start_date, end_date,
                      symb_help):
    """
    This function organizes the functions necessary to run a finished portfolio
    out of sample.
    :param main_wts: Pandas series; how each industry is weighted.
    :param industry_wts: Dictionary where the key is a string of an industry,
    and the value is a pandas series holding how each series in the industry
    is weighted.
    :param cash: Int; the amount of cash to be invested across all industries.
    :param start_date: String; the starting date for running out of sample data.
    YYYY-mm-dd.
    :param end_date: String; the ending date for running out of sample data.
    YYYY-mm-dd.
    :param symb_help: Initialized SymbolHelper class that contains information
    on the symbols being used + their backtesters.
    :return: daily_total, a dataframe holding cash + holdings per day for
    the entire portfolio.
    """
    print("\n\n*** Now running the portfolio on out-of-sample data")
    print("Start date: " + start_date + ", end date: " + end_date)
    daily_total = None  # A dataframe holding cash + holdings per day

    for industry, industry_wt in main_wts.iteritems():
        industry_cash = cash * industry_wt
        print("Running tangency portfolio for (" + industry + ") with $" +
              str(industry_cash))

        for symbol, symbol_wt in industry_wts[industry].iteritems():
            # print('Calculating investment in', symbol)
            symbol_cash = industry_cash * symbol_wt
            # Initialize new 'backtester' that is acting as out-of-sample data
            # First, find what kind of backtester we used in-sample:
            bt_name = symb_help.symbol_backtesters_dict[symbol].name
            bt = backtesters.find_backtester(bt_name, symbol_cash)

            # Then, run the backtester on out-of-sample data
            symbol_data = \
                symb_help.symbol_data_dict[symbol].loc[start_date:end_date, :]
            run_backtester(bt, symbol_data)
            backtesters.organize_backtester(bt)

            # Finally, put the info we got into daily_total
            if daily_total is None:
                daily_total = pd.DataFrame(data=bt.list_total,
                                           index=bt.historical_data.index,
                                           columns=['Total'])
            else:
                daily_total['Total'] = daily_total['Total'] + bt.list_total

    # Calculating excess returns
    finlib.excess_returns(daily_total, risk_free_rate=0.05 / 252,
                          column_name='Total')

    # Summary stats
    print("\nInitial investment in main tangency portfolio:", cash)
    print("Total profit:", round(daily_total.iloc[-1]['Total'] - cash, 2))
    print("Annualized sharpe ratio:",
          round(finlib.get_annualized_sharpe_ratio_df(daily_total), 3))

    return daily_total


def get_symbol_data(start_date, end_date, num_symbols, symb_help,
                    testing=False):
    """
    This function gets all of the symbols for the soon-to-be-created portfolio,
    as well as downloading all of the data necessary for each of those symbols.
    :param start_date: String; the starting date for information that should be
    downloaded for each symbol. YYYY-mm-dd
    :param end_date: String; the ending date for information that should be
    downloaded for each symbol. YYYY-mm-dd
    :param num_symbols: Int; the number of symbols to find for each industry.
    :param symb_help: Initialized SymbolHelper class that contains information
    on the symbols being used + their backtesters.
    :param testing: Bool; a variable that helps speed up the function when
    testing. If True, instead of finding symbols for each industry, only
    the first two industries are used. Default is False.
    :return: Nothing; all information needed is saved into symb_help
    """
    print("\n*** Getting relevant data for every symbol used.")

    # Getting symbols from each GICS industry.
    # It looks like such: {'industry1': ['sym1', 'sym2'], 'industry2': ['sym3']}
    symb_help.obtained_symbols_dict = obtain_symbols.obtain_symbols(
        num_symbols=num_symbols, testing=testing)

    # Get data for each symbol
    print("\nDownloading financial data from yahoo for each symbol")
    for industry in symb_help.obtained_symbols_dict:
        # A list of symbols to be removed in case there is something wrong with
        # yahoo finance; see the if statement below for more info.
        removed_symbols = []

        for symbol in symb_help.obtained_symbols_dict[industry]:
            print("Working with:", symbol)
            symbol_data = finlib.load_financial_data(symbol=symbol,
                                                     start_date=start_date,
                                                     end_date=end_date,
                                                     save=True)

            # Correct number of trading days, to check if dataframe has all info
            num_trading_days = finlib.num_nyse_trading_days(start_date,
                                                            end_date)
            # Collected number of trading days
            symbol_days = symbol_data.loc[start_date:end_date, :].shape[0]

            if symbol_days < num_trading_days:
                # It's possible the symbol data isn't lining up because the
                # downloaded data we have is not up to date. As such, let's
                # check if downloading the data online fixes that.
                test_df = data.DataReader(symbol, 'yahoo', start=start_date,
                                          end=end_date)
                if test_df.loc[start_date:end_date, :].shape[0] == \
                        num_trading_days:
                    print("The data we downloaded is not up to date, so "
                          "it should be redownloaded.")
                    # In this case it's because the downloaded data we have is
                    # not up to date. As such, let's redownload all of it and
                    # redo our info that we got.
                    file_path = '../symbol_data/' + symbol + '.pkl'
                    os.remove(file_path)
                    symbol_data = finlib.load_financial_data(symbol, file_path,
                                                             start_date,  None,
                                                             True)

                    symbol_days = symbol_data.loc[start_date:end_date, :].shape[0]

            if symbol_days < num_trading_days:
                # We couldn't find all of the required data for that symbol
                # becasue of an error in Yahoo Finance. As such, we're going
                # to remove that symbol from our list and get a different
                # symbol from the same industry.
                print(symbol + " doesn't have full yahoo finance info, toss and"
                               " get new symbol")
                new_symbol = obtain_symbols.new_symbol(
                    symbol, industry, symb_help.obtained_symbols_dict[industry])
                if new_symbol is None:
                    # This happens when the program tries to find a new symbol,
                    # but there aren't new symbols in the S&P500 to use (aka all
                    # other symbols are already in the list).
                    print("No new symbol found b/c all others are being used")
                else:
                    # Found a new symbol
                    print("New symbol: " + new_symbol)

                    symb_help.obtained_symbols_dict[industry].append(new_symbol)
                removed_symbols.append(symbol)
                continue

            # We might have more info than we need, so only get info
            # past the starting date.
            symb_help.symbol_data_dict[symbol] = symbol_data.loc[start_date:, :]

        for symbol in removed_symbols:
            # We do this at the end so that we don't mess up the for loop above.
            symb_help.obtained_symbols_dict[industry].remove(symbol)


def get_backtester_data(start_date, end_date, cash, symb_help):
    """
    This function loops through all symbols listed in symb_help in order to
    initialize their backtesters and run them as well.
    :param start_date: String; the starting date for the backtester's data.
    :param end_date: String; the ending date for the backtester's data.
    :param cash: Int; the amount of cash to use in the backtester.
    :param symb_help: Initialized SymbolHelper class that contains information
    on the symbols being used + their backtesters.
    :return: Nothing; all relevant information is saved into symb_help.
    """

    print("\n*** Initializing and running backtesters for each symbol")
    for symbol in symb_help.symbol_data_dict:
        symbol_data = \
            symb_help.symbol_data_dict[symbol].loc[start_date:end_date, :]
        print("Running backtesters for", symbol)
        best_backtester = examine_backtesters(symbol_data, cash=cash)
        symb_help.symbol_backtesters_dict[symbol] = best_backtester


def compare_against_spy(tangency_res, cash, start_date, end_date):
    """
    This function helps compare both in-sample and out-of-sample portfolio data
    against holding SPY, the comparison benchmark used for this trading
    strategy. It figures out how well SPY did profit-wise on its own, as well
    as running a regression analysis between SPY and tangency_res.
    :param tangency_res: A dataframe holding cash + holdings per day; the
    results of the portfolio that will be comapred against SPY.
    :param cash: Int; the amount of cash to be used when holding SPY.
    :param start_date: String; the starting date for holding SPY. YYYY-mm-dd.
    :param end_date: String; the ending date for holding SPY. YYYY-mm-dd.
    :return:
    1) spy_backtester: The backtester used when testing how well SPY did
    in the timeframe given. It holds information that can be useful for further
    computations.
    2) regression_summary: A dictionary holding information pertaining to the
    regression computed between SPY and tangency_res.
    """
    print("\n\n*** Comparing results against spy")

    # Download the data for the regressor
    print("Working with: SPY")
    spy = finlib.load_financial_data('SPY', start_date=start_date,
                                     end_date=end_date)
    spy = spy.loc[start_date:end_date, :]
    # Now let's compare profits
    spy_backtester = examine_backtesters(spy, cash, backtester_names=['HODL'])
    summary = finlib.backtester_summary(spy_backtester)
    print('Initial investment:', summary['Initial Investment'])
    print('Profit:', round(summary['Profit'], 2))
    print('Annualized sharpe ratio:',
          round(summary['Annualized Sharpe Ratio'], 3))

    # Running a regression against SPY
    excess_returns = pd.DataFrame(data=tangency_res['Excess Return'],
                                  index=tangency_res.index,
                                  columns=['Excess Return'])
    finlib.excess_returns(spy, 0.05 / 252, column_name='Adj Close')

    regression_summary = finlib.regression_analysis(
        excess_returns, spy)

    return spy_backtester, regression_summary


def setup_backtesters(cash, num_symbols, start_date, end_date, testing=False):
    """
    The main function that helps create and analyze the randomly generated
    portfolio. All functions above are used in this function.
    :param cash: Int; the amount of money to be invested in the portfolio.
    :param num_symbols: Int; the number of symbols to use in each industry.
    :param start_date: String; the starting date for in-sample data. YYYY-mm-dd.
    :param end_date: String; the ending date for in-sample data. YYYY-mm-dd.
    :param testing: Bool; a variable that helps speed up the function when
    testing. If True, instead of finding symbols for each industry, only
    the first two industries are used. Default is False.
    :return:
    1) wts_tangency_final: A dataframe holding the weights of each industry
    for the final portfolio.
    2) industry_wts: A dictionary, where each key is an industry, and each
    value is the industry's weighing for their symbols.
    3) tangency_res_final: a dataframe that holds net cash + holdings per day
    for the portfolio as a total, after weighing each industry and symbol.
    4) spy_res: The backtester used when testing how well SPY did in the
    timeframe given.
    5) symbol_helper: Initialized SymbolHelper class that contains information
    on the symbols being used + their backtesters.
    6) spy_summary: A dictionary holding information pertaining to the
    regression computed between SPY and the portfolio's results.
    """

    symbol_helper = SymbolsHelper()

    # Getting relevant data for every symbol used
    # End date is none because we want to download all data available
    get_symbol_data(start_date=start_date, end_date=None,
                    num_symbols=num_symbols, testing=testing,
                    symb_help=symbol_helper)

    # Initializing and running backtesters for each symbol
    get_backtester_data(start_date=start_date, end_date=end_date, cash=cash,
                        symb_help=symbol_helper)

    print("\n*** Computing tangency portfolios for each industry")
    industry_wts = {}  # {industry: industry_weight (% of cash to allocate)}
    for industry in symbol_helper.obtained_symbols_dict:
        excess_returns = None  # Dataframe holding excess returns for each ind.
        sharpe_ratio_dict = {}
        for symbol in symbol_helper.obtained_symbols_dict[industry]:
            # Get historical data from each symbol's backtester
            hist_data = \
                symbol_helper.symbol_backtesters_dict[symbol].historical_data

            if excess_returns is None:  # Initializing the dataframe
                excess_returns = pd.DataFrame(index=hist_data.index)
            excess_returns[symbol] = hist_data['Excess Return']

            sharpe_ratio_dict[symbol] = \
                finlib.get_annualized_sharpe_ratio_df(hist_data)

        # Compute tangency portfolio
        wts_tangency, mu_tilde, sigma = \
            finlib.compute_tangency(excess_returns, diagonalize=False)

        sharpe = finlib.get_annualized_sharpe_ratio_wts(wts_tangency, mu_tilde,
                                                        sigma)
        print("Theoretical Sharpe ratio for " + industry + ":",
              round(sharpe, 3))
        industry_wts[industry] = wts_tangency

    industry_excess_returns = None

    print("\n*** Getting excess returns from each industry portfolio")
    for industry in industry_wts:
        print("\nRunning tangency portfolio for (" + industry + ") with $" +
              str(cash))
        tangency_res = run_tangency_portfolio(industry_wts[industry],
                                              cash, symbol_helper)
        profit = tangency_res.iloc[-1]['Total'] - cash
        annualized_sharpe_ratio = \
            finlib.get_annualized_sharpe_ratio_df(tangency_res)
        print("Total profit:", round(profit, 2))
        print("Annualized sharpe ratio:", round(annualized_sharpe_ratio, 3))

        series_data = pd.Series(tangency_res['Excess Return'],
                                index=tangency_res.index, name=industry)

        if industry_excess_returns is None:
            # Initializing the dataframe
            industry_excess_returns = pd.DataFrame(data=series_data,
                                                   index=tangency_res.index)
        else:
            industry_excess_returns = pd.concat([industry_excess_returns,
                                                 series_data], axis=1)

    # Compute tangency portfolio
    wts_tangency_final, mu_tilde, sigma = finlib.compute_tangency(
        industry_excess_returns, diagonalize=False)

    sharpe = finlib.get_annualized_sharpe_ratio_wts(wts_tangency_final,
                                                    mu_tilde, sigma)
    print("\nTheoretical sharpe ratio for the main tangency portfolio:",
          round(sharpe, 3))

    # Running backtest of main tangency portfolio to see its results
    tangency_res_final = run_final_tangency_portfolio(
        wts_tangency_final, industry_wts, cash, symbol_helper
    )

    # Comparing in-sample results against spy
    spy_res, spy_summary = compare_against_spy(tangency_res_final, cash,
                                               start_date=start_date,
                                               end_date=end_date)

    return wts_tangency_final, industry_wts, tangency_res_final, spy_res, \
        symbol_helper, spy_summary


def run_backtesters_out_of_sample(port_wts, indust_wts, cash, start_date,
                                  end_date, symb_help):
    """
    This function runs a created portfolio on data between start_date and
    end_date with those dates typically being out of sample. It also runs
    these results against how well SPY did in the same time period.
    :param port_wts: Pandas series; how each industry is weighted across
    the entire portfolio.
    :param indust_wts: Dictionary where the key is a string of an industry,
    and the value is a pandas series holding how each series in the industry
    is weighted.
    :param cash: Int; The amount of money to invest into the portfolio; an equal
    amount is also invested into SPY.
    :param start_date: String; the starting date to analyze the portfolio/SPY.
    YYYY-mm-dd.
    :param end_date: String; The ending date to analyze the portfolio/SPY.
    YYYY-mm-dd.
    :param symb_help: Initialized SymbolHelper class that contains information
    on the symbols being used + their backtesters.
    :return:
    1) tangency_res: a dataframe that holds net cash + holdings per day
    for the portfolio as a total, after weighing each industry and symbol.
    2) spy_res: SPY's backtester that was run on data between start_date and
    end_date.
    """
    # Running the portfolio on out of sample data
    tangency_res = run_out_of_sample(port_wts, indust_wts, cash,
                                     start_date, end_date, symb_help)

    # Comparing out of sample results against spy
    spy_res, _ = compare_against_spy(tangency_res, cash, start_date=start_date,
                                     end_date=end_date)
    return tangency_res, spy_res

