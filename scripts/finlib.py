"""
This file holds miscellaneous functions relevant to financial trading, such
as obtaining data from yahoo finance, calculating sharpe ratios, finding the
number of nyse trading days between two dates, and more.
"""
import pandas as pd
from pandas_datareader import data
import numpy as np
import statsmodels.api as sm
import sys
from pandas.tseries.offsets import CustomBusinessDay
from pandas.tseries.holiday import get_calendar, HolidayCalendarFactory, \
    GoodFriday
import datetime
import os
from pytz import timezone


def load_financial_data(symbol, output_file=None,
                        start_date='1900-01-01', end_date=None,
                        save=False):
    """
    Returns a dataframe of all of the financial data from a given symbol from
    yahoo. Either obtains it locally or obtains it over the web, and then
    possibly saves it locally as the output_file name.
    :param symbol: A string of the ticker, e.g. 'GOOG'
    :param output_file: Where to find the file.
    :param start_date: Starting date in a string, e.g. '2001-01-01'
    Defaults to '1900', which is one way to just get all of the data
    available.
    :param end_date: Ending date in a string, e.g. '2018-01-01'.
    Defauls to none, where if none, data ends at the most recent trading day.
    :param save: Boolean; Whether to save the file or not. Defaults to False.
    :return: A dataframe of the financial information.
    """
    if output_file is None:
        # Default location to save files
        output_file = '../symbol_data/' + symbol + '.pkl'
    try:
        # Try to read the file first, see what happens
        df = pd.read_pickle(output_file)
        print('File data found...reading data')
    except (FileNotFoundError, ValueError):
        # In this case, we couldn't find the file to read it.
        try:
            # Try to download the data from yahoo finance
            print('File not found...downloading the data')
            df = data.DataReader(symbol, 'yahoo', start=start_date, end=end_date)
            if save:
                if not os.path.isdir('../symbol_data'):
                    # Make the folder symbol_data b/c it doesn't exist
                    os.mkdir('../symbol_data')
                df.to_pickle(output_file)
                print('Data saved.')
        except KeyError as e:
            # In this case, there wasn't data found; there was a problem with
            # yahoo finance.
            print(e)
            sys.exit("There was a problem downloading the yahoo finance data")
    return df


def compute_tangency(excess_return_df, diagonalize=False):
    """
    Compute tangency portfolio given a set of excess returns.
    Also, for convenience, this returns the associated vector of average
    returns and the variance-covariance matrix.
    :param excess_return_df: Pandas Dataframe of at least one column of excess
    returns, but usually 2 or more.
    It wouldn't make sense to call this function with only one column (one
    asset), but there's a valid solution: just put 100% of the investment into
    that asset. As such, no error is raised if there is only one column.
    :param diagonalize: Boolean variable asking whether to diagonalize the
    covariance matrix. This is defaulted to false.
    :return:
    1) Wts_tan: A Series with the index names corresponding to the column names
    for excess_return_df, and the values corresponding to the optimal weight
    for the tangency portfolio.
    2) Mu_tilde: The mean return vector
    3) Sigma: The Covariance matrix (following the desired diagonalization rule)
    """

    Sigma = excess_return_df.cov()  # Covariance matrix.

    if diagonalize:
        # Diagonalizing the matrix gets rid of information, but because this
        # equation involves a Sigma inverse, having data that is slightly wrong
        # compounds into results that are overfitted to the data. As such,
        # diagonalizing can remove that overfitting problem.
        Sigma_D = np.diag(np.diag(Sigma))
        Sigma = Sigma_D

    # n is the number of assets
    n = Sigma.shape[0]  # Shape returns height and width, so we only want one.

    Mu_tilde = excess_return_df.mean()  # Mean return vector.
    sigma_inv = np.linalg.inv(Sigma)  # Inverts the covariance matrix.
    # Normalize the matrix so that it all adds up to one.
    weights = sigma_inv @ Mu_tilde / (np.ones(n) @ sigma_inv @ Mu_tilde)
    # Matrix multiplication with python uses the @ symbol.
    # For convenience we wrap the solution back into a pandas.Series object.
    Wts_tan1 = pd.Series(weights, index=Mu_tilde.index)

    # We don't know whether this is the local minimum or local maximum right
    # now. As such, we need to multiply the tangency weights by -1 and
    # calculate + compare both sharpe ratios of the tangency weights.
    # The portfolio with the higher sharpe ratio is the local maximum, and
    # the portfolio with the lower sharpe ratio is the local minimum.

    Wts_tan2 = Wts_tan1 * -1

    sharpe_ratio1 = get_annualized_sharpe_ratio_wts(Wts_tan1, Mu_tilde, Sigma)
    sharpe_ratio2 = get_annualized_sharpe_ratio_wts(Wts_tan2, Mu_tilde, Sigma)

    if sharpe_ratio1 > sharpe_ratio2:
        Wts_tan = Wts_tan1
    else:
        Wts_tan = Wts_tan2

    return Wts_tan, Mu_tilde, Sigma


def daily_returns(df, column_name):
    """
    Calculates the daily returns for a given column_name in a given dataframe.
    :param df: The dataframe used to find the daily returns
    :param column_name: String; the column used to find the daily returns
    :return: Edits the dataframe in-place, thus requiring no return.
    """
    # Column name is often something like 'Adj Close' or 'Total'
    df['Daily Return'] = df[column_name].pct_change()
    return


def excess_returns(df, risk_free_rate, column_name=None):
    """
    Calculates the excess returns for a given column_name in a given dataframe.
    :param df: The dataframe used to find the excess returns
    :param risk_free_rate: Int; the risk free rate used to find excess returns
    :param column_name: String; the column used to find the daily returns.
    This can also be None if there already is a Daily Return column in the
    dataframe.
    :return: This edits the dataframe in-place, thus requiring no return.
    """
    if 'Daily Return' not in df.columns:
        daily_returns(df, column_name)
    df['Excess Return'] = df['Daily Return'] - risk_free_rate
    return


"""This function has not been properly tested, and as such is commented out 
to emphasize that it is not ready for production use."""
# def cumulative_daily_returns(df, column_name):
#     """
#     Calculates the cumulative daily returns for a given column name in a given
#     dataframe.
#     :param df: The dataframe used to find the cumulative daily returns
#     :param column_name: String; the column used to find the cumul. daily returns
#     :return: The cumulative daily return.
#     """
#     daily_returns(df, column_name)
#
#     # 1 = no change, thus added
#     df['Cumulative Daily Return'] = df['Daily Return'] + 1
#     return df.cumprod()


"""This function has not been properly tested, and as such is commented out
to emphasize that it is not ready for production use."""
# def cumulative_monthly_returns(df, column_name):
#     daily_df = cumulative_daily_returns(df, column_name)
#     monthly_df = daily_df.resample('M').mean()
#     return monthly_df


"""This function has not been properly tested, and as such is commented out
to emphasize that it is not ready for production use."""
# def cumulative_quarterly_returns(df, column_name):
#     daily_df = cumulative_daily_returns(df, column_name)
#     quarterly_df = daily_df.resample('3M').mean()
#     return quarterly_df


"""This function has not been properly tested, and as such is commented out
to emphasize that it is not ready for production use."""
# def find_moving_average(df, window):
#     res_df = df['Adj Close'].rolling(window).mean()
#     return res_df


"""This function has not been properly tested, and as such is commented out
to emphasize that it is not ready for production use."""
# def volatility_over_specified_period(df, column_name, window):
#     daily_returns(df, column_name)
#     df['Adj Close'] = df['Adj Close'].rolling(window).std() * 10
#     return res_df


def get_annualized_sharpe_ratio_df(df):
    """
    When given a dataframe with a column 'Excess Return', returns the
    annualized sharpe ratio.
    Assumes that all data given is daily data.
    :param df: The dataframe used to find the annualized sharpe ratio
    :return: Int, the annualized sharpe ratio.
    """
    annualized_mean = df['Excess Return'].mean() * 252
    annualized_volatility = df['Excess Return'].std() * np.sqrt(252)
    annualized_sharpe_ratio = annualized_mean / annualized_volatility
    return annualized_sharpe_ratio


def get_annualized_sharpe_ratio_wts(wts_tangency, mu_tilde, sigma):
    """
    When given a tangency portfolio, the mean return vector, and the
    covariance matrix, returns the annualized sharpe ratio.
    Assumes that all data given is daily data.
    :param wts_tangency: Pandas series; the tangency portfolio
    :param mu_tilde: Pandas series; the mean return vector.
    :param sigma: Pandas dataframe; the covariance matrix.
    :return: The annualized sharpe ratio.
    """
    mean = mu_tilde @ wts_tangency * 252
    vol = np.sqrt(wts_tangency @ sigma @ wts_tangency) * np.sqrt(252)
    sharpe_ratio = mean / vol
    return sharpe_ratio


def tangency_summary(tangency_res):
    """
    Find the daily return, excess return, and annualized sharpe ratio from
    a dataframe holding the results of a newly implemented portfolio.
    This function assumes that all data is given on a daily basis, and also
    gives an assumption for the daily risk free rate.
    :param tangency_res: Pandas dataframe; holds a column 'Total' that has
    info necessary to calculate all data below.
    :return: The annualized sharpe ratio; additionally, the input variable
    'tangency_res' is edited in-place, and as such returns with the columns
    'Daily Return' and 'Excess Return'.
    """
    tangency_res['Daily Return'] = tangency_res['Total'].pct_change()
    daily_risk_free_rate = 0.05/252
    tangency_res['Excess Return'] = tangency_res['Daily Return'] - \
        daily_risk_free_rate
    annualized_mean = tangency_res['Excess Return'].mean() * 252
    annualized_volatility = tangency_res['Excess Return'].std() * np.sqrt(252)
    annualized_sharpe_ratio = annualized_mean / annualized_volatility
    return annualized_sharpe_ratio


def backtester_summary(bt):
    """
    Summarizes a backtester's results.
    :param bt: A backtester class from the file 'backtesters.py'
    :return: A dictionary containing the annualized sharpe ratio, the initial
    investment amount, and the profit.
    """
    annualized_sharpe_ratio = get_annualized_sharpe_ratio_df(bt.historical_data)
    initial_investment = round(bt.list_total[0], 2)
    profit = bt.list_total[-1] - initial_investment

    summary = {'Annualized Sharpe Ratio': annualized_sharpe_ratio,
               'Initial Investment': initial_investment,
               'Profit': profit}

    return summary


def regression_analysis(regressand_df, regressor_df):
    """
    Computes a regression analysis.
    :param regressand_df: A dataframe holding all regressands for the
    desired regression analysis
    :param regressor_df: A dataframe holding all regressors for the desired
    regression analysis
    :return: A pandas dataframe holding the summary of each regression analysis.
    The summary contains the alpha, beta, r-squared, treynor's ratio, and
    information ratio.
    """
    regressand = regressand_df.columns
    X = sm.add_constant(regressor_df['Excess Return'])
    stats = []
    for y in regressand:
        y = regressand_df[y]
        res = sm.OLS(y, X, missing='drop').fit()
        alpha, beta = res.params
        r_squared = res.rsquared
        treynor_ratio = y.mean() / beta
        information_ratio = alpha / res.resid.std()
        stats.append([alpha, beta, r_squared, treynor_ratio, information_ratio])
    summary = pd.DataFrame(stats, index=regressand,
                           columns=['Alpha', 'Beta', 'R-Squared',
                                    "Treynor's Ratio", 'Information Ratio'])
    return summary


def num_nyse_trading_days(start_date, end_date):
    """
    This function calculates the number of trading days, inclusive, between
    two dates.
    :param start_date: String; the starting date. Has the following format:
    'YYYY-mm-dd'.
    :param end_date: String; the ending date. Has the following format:
    'YYYY-mm-dd'. Can also be None.
    :return: Int; the number of trading days between the two dates.
    """
    """
    Solution for number of trading days found on two stackoverflow posts:
    https://stackoverflow.com/questions/44822697/business-days-between-two-dates-excluding-holidays-in-python
    https://stackoverflow.com/questions/33094297/create-trading-holiday-calendar-with-pandas
    This code isn't perfect because it is directly modifying the USFederal...
    calendar. As in, if I wanted to use it again, I'd have to add back in
    Veteran's Day and Columbus day (that's why I only remove them once).
    To be honest I spent an obnoxious amount of time on this function, trying
    to figure out how to calculate the number of nyse trading days between
    two dates (not just business days, as that's a different question), and
    ultimately I just wanted a solution that would work, even if it was a
    solution that is modifying code I shouldn't be editing. 
    """

    if end_date is None:
        # In this case we weren't given an end date so the end date is assumed
        # to be the current time. Thus we need to find the current time in EST.
        tz = timezone('America/New_York')
        if datetime.datetime.now(tz).time() < datetime.time(9):
            # If it is before 9:00 EST, then the difference is the current date
            # minus the starting date minus 1, because the trading day hasn't
            # started yet.
            end_date = datetime.datetime.now(tz) - datetime.timedelta(days=1)
            end_date = end_date.strftime("%Y-%m-%d")
        else:
            # Else the difference is the current date minus the start date.
            end_date = datetime.datetime.now(tz).strftime("%Y-%m-%d")

    cal = get_calendar('USFederalHolidayCalendar')  # Create calendar
    if len(cal.rules) == 10:
        # If there are 10 rules, then we know we haven't modified this calendar
        # yet.
        # We need to modify this calendar because Veteran's Day and Columbus
        # Day are both trading days.
        cal.rules.pop(7)  # Remove Veteran's Day rule
        cal.rules.pop(6)  # Remove Columbus Day rule
    # Create the calendar from the rules we have.
    tradingCal = HolidayCalendarFactory('TradingCalendar', cal, GoodFriday)
    trading_days = CustomBusinessDay(calendar=tradingCal())
    calendar = pd.date_range(start=start_date, end=end_date,
                             freq=trading_days).to_pydatetime()

    res = len(calendar)
    if datetime.datetime(2018, 12, 5) in calendar:
        # In this case, we need to subtract one because the nyse closed
        # on december 5th, 2018, to mourn George H.W. Bush's death.
        res -= 1
        # Not an elegant solution, but I wasn't sure how else to do it and
        # it seems pretty effective for the days that I'm working with.

    return res


# if __name__ == '__main__':
#     return
