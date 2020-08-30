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
        output_file = '../symbol_data/' + symbol + '.pkl'
    try:
        df = pd.read_pickle(output_file)
        print('File data found...reading data')
    except (FileNotFoundError, ValueError):
        try:
            print('File not found...downloading the data')
            df = data.DataReader(symbol, 'yahoo', start=start_date, end=end_date)
            if save and output_file is not None:
                if not os.path.isdir('../symbol_data'):
                    # Make the folder symbol_data b/c it doesn't exist
                    os.mkdir('../symbol_data')
                df.to_pickle(output_file)
                print('Data saved.')
        except KeyError:
            # In this case, there wasn't data found in the specified time.
            return None
    return df


def compute_tangency(excess_return_df, diagonalize=False):
    """Compute tangency portfolio given a set of excess returns.

    Also, for convenience, this returns the associated vector of average
    returns and the variance-covariance matrix.
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
    # Column name is often something like 'Adj Close' or 'Total'
    df['Daily Return'] = df[column_name].pct_change()
    return


def excess_returns(df, risk_free_rate, column_name=None):
    if 'Daily Return' not in df.columns:
        daily_returns(df, column_name)
    df['Excess Return'] = df['Daily Return'] - risk_free_rate
    return


def cumulative_daily_returns(df, column_name):
    daily_returns(df, column_name)

    # 1 = no change, thus added
    df['Cumulative Daily Return'] = df['Daily Return'] + 1
    return df.cumprod()


def cumulative_monthly_returns(df, column_name):
    daily_df = cumulative_daily_returns(df, column_name)
    monthly_df = daily_df.resample('M').mean()
    return monthly_df


def cumulative_quarterly_returns(df, column_name):
    daily_df = cumulative_daily_returns(df, column_name)
    quarterly_df = daily_df.resample('3M').mean()
    return quarterly_df


def find_moving_average(df, window):
    res_df = df['Adj Close'].rolling(window).mean()
    return res_df


def volatility_over_specified_period(df, column_name, window):
    # NOTE: This function needs to be checked, as I'm unsure what the * 10 means
    # as of right now.
    daily_returns(df, column_name)
    df['Adj Close'] = df['Adj Close'].rolling(window).std() * 10
    sys.exit("Volatility_over_specified_period shouldn't be used yet")
    return res_df


def get_annualized_sharpe_ratio_df(df):
    annualized_mean = df['Excess Return'].mean() * 252
    annualized_volatility = df['Excess Return'].std() * np.sqrt(252)
    annualized_sharpe_ratio = annualized_mean / annualized_volatility
    return annualized_sharpe_ratio


def get_annualized_sharpe_ratio_wts(wts_tangency, mu_tilde, sigma):
    mean = mu_tilde @ wts_tangency * 252
    vol = np.sqrt(wts_tangency @ sigma @ wts_tangency) * np.sqrt(252)
    sharpe_ratio = mean / vol
    return sharpe_ratio


def tangency_summary(tangency_res):
    tangency_res['Daily Return'] = tangency_res['Total'].pct_change()
    daily_risk_free_rate = 0.05/252
    tangency_res['Excess Return'] = tangency_res['Daily Return'] - \
        daily_risk_free_rate
    annualized_mean = tangency_res['Excess Return'].mean() * 252
    annualized_volatility = tangency_res['Excess Return'].std() * np.sqrt(252)
    annualized_sharpe_ratio = annualized_mean / annualized_volatility
    return annualized_sharpe_ratio


def backtester_summary(bt):
    annualized_sharpe_ratio = get_annualized_sharpe_ratio_df(bt.historical_data)
    initial_investment = round(bt.list_total[0], 2)
    profit = bt.list_total[-1] - initial_investment
    # average_annual_gain = profit/initial_investment * 100 / 2

    summary = {'Annualized Sharpe Ratio': annualized_sharpe_ratio,
               'Initial Investment': initial_investment,
               'Profit': profit}

    return summary


def regression_analysis(regressand_df, regressor_df):
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
    # Solution for number of trading days found on two stackoverflow posts:
    # https://stackoverflow.com/questions/44822697/business-days-between-two-dates-excluding-holidays-in-python
    # https://stackoverflow.com/questions/33094297/create-trading-holiday-calendar-with-pandas
    # This code isn't perfect because it is directly modifying the USFederal...
    # calendar. As in, if I wanted to use it again, I'd have to add back in
    # Veteran's Day and Columbus day (that's why I only remove them once).
    # To be honest I spent an obnoxious amount of time on this function, trying
    # to figure out how to calculate the number of nyse trading days between
    # two dates (not just business days, as that's a different question), and
    # ultimately I just wanted a solution that would work, even if it was a
    # solution that is modifying code I shouldn't be editing. Thankfully we
    # won't be using USFederalHolidayCalendar any other time in this code, so
    # it can be kept in here, and this long block text will show that there's a
    # problem that should be solved right here.
    if end_date is None:
        tz = timezone('America/New_York')
        if datetime.datetime.now(tz).time() < datetime.time(9):
            end_date = datetime.datetime.now(tz) - datetime.timedelta(days=1)
            end_date = end_date.strftime("%Y-%m-%d")
        else:
            end_date = datetime.datetime.now(tz).strftime("%Y-%m-%d")

    cal = get_calendar('USFederalHolidayCalendar')  # Create calendar
    if len(cal.rules) == 10:
        cal.rules.pop(7)  # Remove Veteran's Day rule
        cal.rules.pop(6)  # Remove Columbus Day rule
    tradingCal = HolidayCalendarFactory('TradingCalendar', cal, GoodFriday)
    trading_days = CustomBusinessDay(calendar=tradingCal())
    calendar = pd.date_range(start=start_date, end=end_date,
                             freq=trading_days).to_pydatetime()

    res = len(calendar)
    if datetime.datetime(2018, 12, 5) in calendar:
        res -= 1  # George H.W. Bush day of mourning
        # Not the most elegant solution, but I wasn't sure how else to do it and
        # it seems pretty effective for the days that I'm working with.

    return res


# if __name__ == '__main__':
#     return
