"""
This file helps graph data obtained from previous runs saved from
stat_analysis.py.
"""
import run_backtesters as rb
import matplotlib.pyplot as plt
import stat_analysis
import pandas as pd
import numpy as np
import sys


def profit_scatterplot(start_date_in, end_date_in, start_date_out, end_date_out,
                       num_symbols, file_name):
    """
    This function helps graph a scatterplot of the in-sample and out of sample
    profits for a given sample set.
    Note: As of now there are still small variables that need to be edited
    in the function, variables that are purely visual. These are denoted with
    the comment "# visual edit".
    :param start_date_in: String; starting date for in-sample data. YYYY-mm-dd.
    :param end_date_in: String; ending date for in-sample data. YYYY-mm-dd.
    :param start_date_out: String; start date for out sample data. YYYY-mm-dd.
    :param end_date_out: String; end date for out sample data. YYYY-mm-dd.
    :param num_symbols: Number of symbols used per industry.
    :param file_name: String; the name of the file when saved.
    :return:
    """
    # Getting data
    stats = pd.read_csv('../statistics/summary_stats.csv')

    # Organizing stats by rows that meet correct sample requirements
    stats = stats[(stats.num_symbols == num_symbols) &
                  (stats.start_date_insample == start_date_in) &
                  (stats.end_date_insample == end_date_in) &
                  (stats.start_date_outsample == start_date_out) &
                  (stats.end_date_outsample == end_date_out)]
    sample_size_orig = stats.shape[0]
    print("Sample size:", sample_size_orig)

    # Organizing stats by profits that aren't outliers
    stats = stats[(stats.profit_insample < 4000000) &  # Visual edit
                  (stats.profit_outsample < 1500000)]  # Visual edit
    sample_size = stats.shape[0]
    outliers = sample_size_orig - sample_size
    print("Outliers:", outliers)
    print("Finalized sample size:", sample_size)
    x = stats['profit_insample']
    y = stats['profit_outsample']
    plt.scatter(x, y, 3, c='#135b75', label='Portfolio results')  # Visual edit

    # Setting up SPY data
    x_spy = stats['spy_profits_insample'].iloc[0]
    y_spy = stats['spy_profits_outsample'].iloc[0]
    plt.scatter(x_spy, y_spy, 15, c='#f0a029', label='SPY results')  # Visual edit

    # Creating a line emphasizing where SPY is
    plt.axhline(y=y_spy, linewidth=1, color='#f0a029', alpha=0.5,
                label='SPY, extended')  # Visual edit

    # Creating a line that emphasizes the relationship between in-sample and
    # out of sample profits
    profit_summary = stat_analysis.regression_analysis_simple(
        y=stats['profit_outsample'], x=stats['profit_insample']
    )
    print("Linspace")
    x = np.linspace(500000, 3500000, 100)  # Visual edit
    y = profit_summary['alpha'] + profit_summary['beta'] * x
    print("Linspace2")
    plt.plot(x, y, lw=1, label='Portfolio best fit', alpha=0.5)  # Visual edit

    # Labeling graph
    title = 'SPY Profits Versus Portfolio Profits, Overall\n' + \
            start_date_out + ' -- ' + end_date_out + \
            ', symbols per industry = ' + str(num_symbols)
    plt.title(title)
    plt.xlabel('In-Sample Profits')
    plt.ylabel('Out of Sample Profits')
    plt.legend()

    # Save the file
    plt.savefig('../img/' + file_name, dpi=300)

    # Show the file
    plt.show()


def plot_data(data, labels, file_name, xlabel='', ylabel='', title=''):
    """
    Plots data onto a singular plot.
    :param data: A list holding lists of revenues. The data for the graph.
    :param labels: A list holding lists of strings. The labels to the graphs for
    the legend.
    :param file_name: String; name of the file when saved.
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

    # Save the file
    plt.savefig('../img/' + file_name, dpi=300)

    # Show the graph
    plt.show()


def compare_multiple_runs_of_program(cash, num_runs, start_date_in, end_date_in,
                                     start_date_out, end_date_out, num_symbols,
                                     file_name_in, file_name_out,
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
    :param file_name_in: String, name of to-be-made-graph for in-sample data
    :param file_name_out: String, name of to-be-made-graph for out-sample data
    :param testing: Bool; Whether to use all 11 GICS industries (True), or
    whether to only use 2, speeding up the calculations (False).
    :return: Two plots are put on SciView.
    """

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
        title=title,
        file_name=file_name_in
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
        title=title,
        file_name=file_name_out
    )


if __name__ == '__main__':
    profit_scatterplot('2018-01-01', '2020-01-01', '2020-01-01', '2020-07-01',
                       5, 'corona_5_scatter.png')
    compare_multiple_runs_of_program(1000000, 4, '2018-01-01', '2020-01-01',
                                     '2020-01-01', '2020-07-01', 5,
                                     'corona_5_in.png', 'corona_5_out.png')
