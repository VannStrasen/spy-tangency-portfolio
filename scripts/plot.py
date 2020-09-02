import run_backtesters as rb
import matplotlib.pyplot as plt
import sys


def plot_data(data, labels, xlabel='', ylabel='', title=''):
    """
    Plots data onto a singular plot.
    :param data: A list holding lists of revenues. The data for the graph.
    :param labels: A list holding lists of strings. The labels to the graphs for
    the legend.
    :param xlabel: String; the x label.
    :param ylabel: String; the y label.
    :param title: String; the title.
    :return: A plot is placed into SciView.
    """

    # Plot the data first
    plt.plot()
    for i in range(0, len(data)):
        # The data that is given is in revenue, so let's make it profit.
        data[i] = [x - data[i][0] for x in data[i]]

        # Plot it with the respective label.
        plt.plot(data[i], label=labels[i])

    # Now let's organize the plot
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.show()


def compare_multiple_runs_of_program(cash, num_runs, start_date_in, end_date_in,
                                     start_date_out, end_date_out, num_symbols,
                                     testing=False):
    """
    This function plots in-sample and out of sample profits for multiple runs
    of the portfolio created in run_backtesters.py against SPY profits.
    It does so by running the functions in run_backtesters.py necessary to
    get profits, and then passes off the results to the function plot_data()
    for the actual plotting
    :param cash: Int; the amount of money to use in a portfolio
    :param num_runs: Int; The amount of portfolios to be generated and plotted.
    :param start_date_in: String; In-sample starting date. YYYY-mm-dd.
    :param end_date_in: String; In-sample ending date. YYYY-mm-dd.
    :param start_date_out: String; Out-sample starting date. YYYY-mm-dd.
    :param end_date_out: String; Out-sample ending date. YYYY-mm-dd.
    :param num_symbols: Int; number of symbols to work with in each industry.
    :param testing: Bool; Whether to use all 11 GICS industries (True), or
    whether to only use 2, speeding up the calculations (False).
    :return: Two plots are put on SciView.
    """
    # """

    # :param cash: The amount of money to be allocated to the portfolio/SPY.
    # :param num_runs: The amount of runs to be plotted together.
    # :return: Two pyplot plots, one of in-sample profits, and another with
    # out of sample profits.
    # """

    # *********** In sample functions ********************************

    # Lists to hold results from rb.setup_backtesters
    portfolio_wts_list = []
    industry_wts_list = []
    insample_data = []
    symbol_helper_list = []
    spy_data = None

    # Getting information from portfolios in sample
    for x in range(0, num_runs):
        p, i, t, s, s_h, _ = rb.setup_backtesters(
            cash=cash, num_symbols=num_symbols, start_date=start_date_in,
            end_date=end_date_in, testing=testing)
        portfolio_wts_list.append(p)
        industry_wts_list.append(i)
        symbol_helper_list.append(s_h)
        insample_data.append(t['Total'].tolist())
        if x == 0:
            spy_data = s  # Only need to save it once.
    insample_data.append(spy_data.list_total)

    # Now let's plot our results
    title = 'Comparing Multiple Porfolios, In-Sample Results\n' + \
            start_date_in + ' -- ' + end_date_in + \
            ', symbols per industry = ' + str(num_symbols)
    plot_data(
        data=insample_data,
        labels=['Portfolio 1', 'Portfolio 2', 'Portfolio 3', 'Portfolio 4',
                'S&P500 if held'],
        xlabel='Days since strategy began',
        ylabel='Total profit',
        title=title
    )

    # **************** Out of sample functions *************************

    # Places to hold results from out of sample functions
    outsample_data = []
    spy_data = None

    # Getting information from running portfolios out of sample
    for i in range(0, num_runs):
        t, s = rb.run_backtesters_out_of_sample(
            portfolio_wts_list[i], industry_wts_list[i], cash=cash,
            start_date=start_date_out, end_date=end_date_out,
            symb_help=symbol_helper_list[i]
        )
        outsample_data.append(t['Total'].tolist())
        if i == 0:
            spy_data = s  # Only need to save it once
    outsample_data.append(spy_data.list_total)

    # Now let's plot our results
    title = 'Comparing Multiple Porfolios, Out-of-Sample Results\n' + \
            start_date_out + ' -- ' + end_date_out + \
            ', symbols per industry = ' + str(num_symbols)
    plot_data(
        data=outsample_data,
        labels=['Portfolio 1', 'Portfolio 2', 'Portfolio 3', 'Portfolio 4',
                'S&P500 if held'],
        xlabel='Days since strategy began',
        ylabel='Total Profit',
        title=title
    )


if __name__ == '__main__':
    compare_multiple_runs_of_program(1000000, 4, '2019-01-01', '2020-01-01',
                                     '2020-01-01', '2020-07-01', 2, True)
