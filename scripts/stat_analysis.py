"""
This file helps save and analyze information obtained by running the backtesters
in run_backtesters.py. The two functions to begin with are:
1) download_data() -> To begin saving the data obtained
2) analyze_summary_stats() -> To analyze the data obtained.
"""
import finlib
import run_backtesters as rb
import plot
import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
import sys
import scipy.stats


def download_backtest_stats(cash, num_symbols, start_date_insample,
                            end_date_insample, start_date_outsample,
                            end_date_outsample, plot_bool=False):
    """
    This function's ultimate job is to save all information obtained when
    testing a portfolio through backtesters with in-sample data, and
    the results obtained when running the same portfolio on out-of-sample data.
    It does so by using the parameters to call functions from run_backtesters.py
    and save the outputs into the file 'statistics/summary_stats.csv'. Data
    includes info like backtester profits, sharpe ratios, number of symbols
    used, as well as info from holding SPY during the same time period.
    :param cash: The amount of cash to be used in the portfolio
    :param num_symbols: The number of symbols to be used in each industry.
    :param start_date_insample: The starting date for testing backtesters.
    :param end_date_insample: The ending date for testing backtesters.
    :param start_date_outsample: The starting date for running the portfolio
    over data not used to create it.
    :param end_date_outsample: The ending date for running the portfolio over
    data not used to create it.
    :param plot_bool: Default false; a boolean value that prints out plots
    of the profits obtained. Not recommended to be used when running this
    function often (such as overnight), as that will slow the program down
    and take up a lot of memory.
    :return: Appends all information obtained (as seen in the dictionary
    'stats') into the file 'statistics/summary_stats.csv'.
    """
    # Main dict that we'll use to save all statistics.
    stats = {}

    # In-sample information
    wts_tangency, industry_wts, tangency_res, spy_res, symbol_helper, spy_sum = \
        rb.setup_backtesters(cash=cash, num_symbols=num_symbols,
                             start_date=start_date_insample,
                             end_date=end_date_insample)

    if plot_bool:
        plot.plot_in_sample_run(
            data=[tangency_res['Total'].tolist(), spy_res.list_total],
            labels=['Tangency profits in sample: ' + start_date_insample +
                    ' -- ' + end_date_insample, 'S&P500 returns if held']
        )

    # Let's put in data we have already right now.
    stats['num_symbols'] = num_symbols
    stats['initial_investment'] = cash
    stats['symbols'] = str(symbol_helper.obtained_symbols_dict)
    stats['start_date_insample'] = start_date_insample
    stats['end_date_insample'] = end_date_insample
    stats['profit_insample'] = tangency_res.iloc[-1]['Total'] - cash
    stats['spy_profits_insample'] = spy_res.list_total[-1] - cash
    stats['annualized_sharpe_ratio_insample'] = \
        finlib.get_annualized_sharpe_ratio_df(tangency_res)
    stats['alpha_insample'] = spy_sum.iloc[0]['Alpha']
    stats['beta_insample'] = spy_sum.iloc[0]['Beta']
    stats['r-squared_insample'] = spy_sum.iloc[0]['R-Squared']
    stats['treynors_ratio_insample'] = spy_sum.iloc[0]["Treynor's Ratio"]
    stats['information_ratio_insample'] = spy_sum.iloc[0]["Information Ratio"]
    stats['start_date_outsample'] = start_date_outsample
    stats['end_date_outsample'] = end_date_outsample

    # Out of sample information
    outsample_res = rb.run_out_of_sample(
        wts_tangency, industry_wts, cash=1000000, start_date=start_date_outsample,
        end_date=end_date_outsample, symb_help=symbol_helper
    )
    spy_res, spy_sum = rb.compare_against_spy(outsample_res, cash,
                                              start_date_outsample,
                                              end_date_outsample)

    # More data to ultimately save into the csv.
    stats['profit_outsample'] = outsample_res.iloc[-1]['Total'] - cash
    stats['spy_profits_outsample'] = spy_res.list_total[-1] - cash
    stats['annualized_sharpe_ratio_outsample'] = \
        finlib.get_annualized_sharpe_ratio_df(outsample_res)
    stats['alpha_outsample'] = spy_sum.iloc[0]['Alpha']
    stats['beta_outsample'] = spy_sum.iloc[0]['Beta']
    stats['r-squared_outsample'] = spy_sum.iloc[0]['R-Squared']
    stats['treynors_ratio_outsample'] = spy_sum.iloc[0]["Treynor's Ratio"]
    stats['information_ratio_outsample'] = spy_sum.iloc[0]["Information Ratio"]

    if plot_bool:
        plot.plot_out_of_sample_run(
            data=[outsample_res['Total'].tolist(), spy_res.list_total],
            labels=['Tangency profits out of sample: ' + start_date_outsample +
                    ' -- ' + end_date_outsample, 'S&P500 profits'],
            axes=0
        )

    # Now let's save the information to a csv.
    print("Saving to csv")
    df = pd.DataFrame(data=stats, index=[0])
    path = '../statistics/summary_stats.csv'
    if os.path.exists(path) is False:
        # If this somehow is false, let's save the stats to a different file and
        # quit the program (as this shouldn't happen).
        df.to_csv('../statistics/summary_stats_new.csv', index=False)
        sys.exit(path + " does not exist.")
    else:
        # I was having problems appending the data to the csv directly. While
        # this is slower than doing as such, it solve the problem by copying
        # the entire csv into a dataframe, appending the data to said dataframe,
        # and then overwriting the old file with that dataframe.
        # This would be a great place to increase the speed of this function,
        # especially as 'statistics/summary_stats_
        df_old = pd.read_csv(path)
        df_new = df_old.append(df, ignore_index=True)
        df_new.to_csv(path, index=False)
    print("Csv saved")


def regression_analysis_simple(y, x):
    """
    This function computes a simple regression analysis.
    :param y: The regressand; typically a pandas series.
    :param x: The regressor; typically a pandas series.
    :return: A dictionary containing the alpha, beta, and r-squared values
    of the regression.
    """
    summary = {}
    x = sm.add_constant(x)
    res = sm.OLS(y, x).fit()
    summary['alpha'], summary['beta'] = res.params
    summary['r_squared'] = res.rsquared
    return summary


def mean_confidence_interval(stats, confidence=0.95):
    """
    This function executes a mean confidence interval.
    :param stats: The data to be analyzed, typically a pandas series.
    :param confidence: The confidence range for the interval; defaults to 0.95,
    AKA creating a confidence interval where alpha = 0.05.
    :return: The confidence interval, including the lower bound, upper bound,
    and mean of the data given.
    """
    array = 1.0 * np.array(stats)
    mean = np.mean(array)
    std_err = scipy.stats.sem(array)
    diff = std_err * scipy.stats.t.ppf((1 + confidence) / 2.0, len(array) - 1)
    return mean-diff, mean, mean+diff


def analyze_summary_stats(num_symbols, start_date_insample, end_date_insample,
                          start_date_outsample, end_date_outsample):
    """
    This function calculates relevant statistics from data obtained previously,
    as saved in the file 'statistics/summary_stats.csv'. The parameters are each
    used to identify which subsample of data that should be analyzed.
    :param num_symbols: The number of symbols used in the desired portfolio
    :param start_date_insample: The in-sample start date used in the desired
    portfolio
    :param end_date_insample: The in-sample end date used in the desired
    portfolio
    :param start_date_outsample: The out of sample start date used in the
    desired portfolio
    :param end_date_outsample: The out of sample end date used in the desired
    portfolio
    :return: Prints out statistics and information about the portfolio as
    follows:
    -- Sample size
    -- Alpha, beta, and r-squared of a linear regression between in-sample and
    out of sample annualized sharpe ratios
    -- Alpha, beta, and r-squared of a linear regression between in-sample and
    out of sample profits for the portfolio
    -- Alpha, beta, and r-squared of a linear regression between in-sample and
    out of sample profits for the portfolio, minus the profits for the S&P 500
    held during the same time period with the same initial investment.
    -- 95% confidence interval of the out of sample annualized sharpe ratio
    -- 95% confidence interval of the out of sample portfolio profits
    -- 95% confidence interval of the out of sample portfolio profits minus the
    respective S&P 500 profits.
    """

    print("\n\n*** Statistical analysis for the following backtest:")
    print("Number of symbols:", num_symbols)
    print("In-sample:", start_date_insample + " -- " + end_date_insample)
    print("Out-of-sample:", start_date_outsample + " -- " + end_date_outsample)
    stats = pd.read_csv('../statistics/summary_stats.csv')
    stats = stats[(stats.num_symbols == num_symbols) &
                  (stats.start_date_insample == start_date_insample) &
                  (stats.end_date_insample == end_date_insample) &
                  (stats.start_date_outsample == start_date_outsample) &
                  (stats.end_date_outsample == end_date_outsample)]
    print("Sample size:", stats.shape[0])

    print("\nLinear regression between in-sample & out of sample sharpe ratios:")
    sharpe_summary = regression_analysis_simple(
        y=stats['annualized_sharpe_ratio_outsample'],
        x=stats['annualized_sharpe_ratio_insample']
    )
    print("Alpha:", sharpe_summary['alpha'])
    print("Beta:", sharpe_summary['beta'])
    print("R-squared:", sharpe_summary['r_squared'])

    print("\nLin reg between in-sample and out-sample portfolio profits:")
    profit_summary = regression_analysis_simple(
        y=stats['profit_outsample'], x=stats['profit_insample']
    )
    print("Alpha:", profit_summary['alpha'])
    print("Beta:", profit_summary['beta'])
    print("R-squared:", profit_summary['r_squared'])

    print("\nLin reg between in-sample and out-sample portfolio profits \n"
          "minus in-sample and out-sample spy profits, respectively:")
    net_profit_insample = stats['profit_insample'] - \
        stats['spy_profits_insample']
    net_profit_outsample = stats['profit_outsample'] - \
        stats['spy_profits_outsample']

    net_profit_summary = regression_analysis_simple(
        y=net_profit_outsample, x=net_profit_insample
    )
    print("Alpha:", net_profit_summary['alpha'])
    print("Beta:", net_profit_summary['beta'])
    print("R-squared:", net_profit_summary['r_squared'])

    print("\n95% confidence interval for out-sample annualized sharpe ratio:")
    print(mean_confidence_interval(stats['annualized_sharpe_ratio_outsample']))
    print("\n95% confidence interval for out-sample profits:")
    print(mean_confidence_interval(stats['profit_outsample']))
    print("\n95% confidence interval for out-sample profits minus SPY profits:")
    print(mean_confidence_interval(net_profit_outsample))


def download_data(ignore_errors):
    """
    This function is a wrapper used to help download data; it helps organize
    whether the program should stop completely when it sees an error, or keep
    running (a trait that is useful overnight when you'd want to download
    multiple hours worth of data and you know the program generally works).
    :param ignore_errors: A boolean variable; true if you want the program to
    keep going when it receives an error, false if you want the program to stop
    when it receives an error.
    :return: Ultimately saves data to the file 'statistics/summary_stats.csv'
    """
    def samples_to_run():
        """
        Collects and saves data using the function download_backtest_stats().
        If the user wants to record different data, it should be done directly
        here.
        :return: Ultimately saves data to the file
        'statistics/summary_stats.csv'
        """
        download_backtest_stats(1000000, 5, '2017-01-01', '2019-01-01',
                                '2019-01-01', '2020-01-01')
        download_backtest_stats(1000000, 10, '2017-01-01', '2019-01-01',
                                '2019-01-01', '2020-01-01')
        download_backtest_stats(1000000, 20, '2017-01-01', '2019-01-01',
                                '2019-01-01', '2020-01-01')
        download_backtest_stats(1000000, 5, '2018-01-01', '2020-01-01',
                                '2020-01-01', '2020-07-01')
    if ignore_errors:
        while True:
            try:
                samples_to_run()
            except Exception as e:
                print(e)
                continue
    else:
        while True:
            samples_to_run()


if __name__ == '__main__':
    download_data(ignore_errors=False)
    # analyze_summary_stats(num_symbols=5,
    #                       start_date_insample='2017-01-01',
    #                       end_date_insample='2019-01-01',
    #                       start_date_outsample='2019-01-01',
    #                       end_date_outsample='2020-01-01')
    # analyze_summary_stats(num_symbols=10,
    #                       start_date_insample='2017-01-01',
    #                       end_date_insample='2019-01-01',
    #                       start_date_outsample='2019-01-01',
    #                       end_date_outsample='2020-01-01')
    # analyze_summary_stats(num_symbols=20,
    #                       start_date_insample='2017-01-01',
    #                       end_date_insample='2019-01-01',
    #                       start_date_outsample='2019-01-01',
    #                       end_date_outsample='2020-01-01')
    # analyze_summary_stats(num_symbols=5,
    #                       start_date_insample='2018-01-01',
    #                       end_date_insample='2020-01-01',
    #                       start_date_outsample='2020-01-01',
    #                       end_date_outsample='2020-07-01')
