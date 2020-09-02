import run_backtesters as rb
import matplotlib.pyplot as plt
import numpy as np
import sys


def plot_in_sample_run(data, labels):
    """
    Given data and labels, create a pyplot plot to visualize the data.
    :param data: A list where each index is another list of data that should
    be plotted. Each index in 'data' thus becomes a line visualized on one plot.
    :param labels: What each index in 'data' should be labeled as.
    :return: A plot.
    """
    plt.plot()
    for i in range(0, len(data)):
        # The data that is given is in revenue, so let's make it profit.
        data[i] = [x - data[i][0] for x in data[i]]

        # Plot it with the respective label.
        plt.plot(data[i], label=labels[i])
    plt.xlabel('# of days the strategy has run')
    plt.ylabel('Profits')
    if len(data) <= 2:
        plt.title('In-sample backtester vs SPY')
    else:
        plt.title('In-sample backtesters vs SPY')
    plt.legend()
    plt.show()
    return


def plot_out_of_sample_run(data, labels, axes):
    """

    :param data:
    :param labels:
    :param axes:
    :return:
    """
    plt.plot()

    for i in range(0, len(data)):
        # The data that is given is in revenue, so let's make it profit.
        data[i] = [x - data[i][0] for x in data[i]]

        # Plot it with the respective label.
        plt.plot(data[i], label=labels[i])
    for i in range(1, axes + 1):
        num_days = len(data[0])
        x = np.floor(i * num_days/(axes + 1))
        plt.axvline(x, 0, 1, color='black')

    plt.xlabel('# of days the strategy has run')
    plt.ylabel('Profits')
    if len(data) <= 2:
        plt.title('Out-of-sample backtester vs SPY')
    else:
        plt.title('Out-of-sample backtesters vs SPY')
    plt.legend()
    plt.show()
    return


def compare_multiple_runs_of_program(cash, num_runs):
    """
    This function plots in-sample and out of sample profits for multiple runs
    of the portfolio created in run_backtesters.py against SPY profits.
    It does so by running the functions in run_backtesters.py necessary to
    get profits, and then passes off the results to the functions
    'plot_in_sample_run()' and 'plot_out_of_sample_run() for the actual
    plotting.
    :param cash: The amount of money to be allocated to the portfolio/SPY.
    :param num_runs: The amount of runs to be plotted together.
    :return: Two pyplot plots, one of in-sample profits, and another with
    out of sample profits.
    """
    portfolio_wts_list = []
    industry_wts_list = []
    insample_data = []
    symbol_helper_list = []
    spy_data = None
    for x in range(0, num_runs):
        p, i, t, s, s_h, _ = rb.setup_backtesters(
            cash=cash, num_symbols=5, start_date='2019-01-01',
            end_date='2020-01-01', testing=False)
        portfolio_wts_list.append(p)
        industry_wts_list.append(i)
        symbol_helper_list.append(s_h)
        insample_data.append(t['Total'].tolist())
        if x == 0:
            spy_data = s  # Only need to save it once.
    insample_data.append(spy_data.list_total)

    plot_in_sample_run(
        data=insample_data,
        labels=['Portfolio1 profits', 'Portfolio2 profits',
                'Portfolio3 profits', 'Portfolio4 profits',
                'S&P500 profits if held']
    )

    outsample_data = []
    spy_data = None
    for i in range(0, num_runs):
        t, s = rb.run_backtesters_out_of_sample(
            portfolio_wts_list[i], industry_wts_list[i], cash=cash,
            start_date='2020-01-01', end_date='2020-07-01',
            symb_help=symbol_helper_list[i]
        )
        outsample_data.append(t['Total'].tolist())
        if i == 0:
            spy_data = s  # Only need to save it once
    outsample_data.append(spy_data.list_total)
    plot_out_of_sample_run(
        data=outsample_data,
        labels=['Portfolio1 profits', 'Portfolio2 profits',
                'Portfolio3 profits', 'Portfolio4 profits',
                'S&P500 profits if held'],
        axes=0
    )


if __name__ == '__main__':
    compare_multiple_runs_of_program(1000000, 4)
