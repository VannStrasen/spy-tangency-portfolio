import pandas as pd
import random
import sys
import os
import finlib

pd.set_option('display.max_columns', 500)


def organize_symbols(testing=False):
    """
    Gets all stocks in the s&p500, and organizes them by GICS sector.
    :param testing: A boolean variable that, if true, cuts the number of
    industries gathered from 11 to 2. This greatly speeds up testing so that
    latter parts of the code can be reached sooner.
    :return: Dictionary where the key is the sector, and the value is a
    list of all symbols in that industry in the s&p500.
    """
    print("Reading wikipedia")  # Vann: Make this local.
    table = pd.read_html(
        'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    df = table[0]

    stock_sectors = {}  # Holds stocks split up by GICS sectors
    for index, row in df.iterrows():
        # These stocks don't have full info on yahoo finance, so let's get rid
        # of them now so that we don't think we can use them.
        bad_stocks = ['FOX', 'FOXA', 'TT']
        symbol = row['Symbol'].replace('.', '-')  # Yahoo finance uses dashes
        if symbol in bad_stocks:
            continue

        date_added = row['Date first added']

        # Only have information on date if it is a string.
        if isinstance(date_added, str) and int(date_added[:4]) < 2016:
            # Only want stocks that at least have info past 2016. While this
            # does get rid of some stocks that have info past 2016 (this is
            # their date added into the s&p 500), this is good enough for this
            # project.

            sector = row['GICS Sector']

            if sector not in stock_sectors:
                stock_sectors[sector] = [symbol]
            else:
                stock_sectors[sector].append(symbol)

    if testing is True:
        # In this case, we cut out 9 of the GICS sectors because we want to
        # speed up testing (AKA not because we think this will create a better
        # model).
        temp_result = {'Industrials': stock_sectors['Industrials'],
                       'Health Care': stock_sectors['Health Care']}
        stock_sectors = temp_result
    return stock_sectors


def get_random_symbols(dict_of_symbols, num_symbols):
    """
    Randomly picks num_symbols symbols from the s&p 500 in each GICS industry.
    :param dict_of_symbols: Dictionary where the key is the sector, and the
    value is a list of all symbols in that industry in the s&p500.
    This is the result of organize_symbols().
    :param num_symbols: Number of symbols to get per industry.
    :return: A dictionary where the key is the sector, and the value is a list
    of 10 randomly chosen symbols from the list in dict_of_symbols.
    """
    res = {}
    for industry in dict_of_symbols:
        symbols = dict_of_symbols[industry]
        try:
            num_symbols_per_industry = num_symbols
            res[industry] = random.sample(symbols, num_symbols_per_industry)
        except ValueError:
            # There were less than 10 symbols in the list. Just set the result
            # as the full list.
            res[industry] = symbols
        print(industry + ":", res[industry])

    return res


def new_symbol(removed_symbol, industry, symbol_list):
    stock_sectors = organize_symbols()
    for symbol in stock_sectors[industry]:
        if symbol != removed_symbol and (symbol not in symbol_list):
            return symbol


def obtain_symbols(num_symbols, testing=False):
    """
    Organizational function; obtains a list of 10 symbols for each GICS industry
    from the S&P 500.
    :param num_symbols: Number of symbols to get per industry
    :param testing: A boolean variable that, if true, cuts the number of
    industries gathered from 11 to 2. This greatly speeds up testing so that
    latter parts of the code can be reached sooner.
    :return: A dictionary where the key is the sector, and the value is a list
    of 10 randomly chosen symbols.
    """
    dict_of_symbols = organize_symbols(testing=testing)
    symbols = get_random_symbols(dict_of_symbols, num_symbols)
    return symbols


def download_sp500_symbols(delete=False):
    if delete:
        path = '../symbol_data/'
        for file in os.listdir(path):
            os.remove(path + file)

    stock_sectors = organize_symbols()
    for industry in stock_sectors:
        for symbol in stock_sectors[industry]:
            print('Downloading', symbol)
            finlib.load_financial_data(symbol, start_date='2015-01-01',
                                       end_date=None, save=True)
    print('Downloading SPY')
    finlib.load_financial_data('SPY', start_date='2015-01-01', end_date=None,
                               save=True)


if __name__ == '__main__':
    download_sp500_symbols()
