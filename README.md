# spy-tangency-portfolio
Randomized portfolio builder I made over the summer of 2020.

The key takeaway from this project is that building a tangency portfolio out of historical stock data can (on average) create a profitable portfolio, even if you don't know anything in-depth about the sector/company you're investing in.

## Inspiration for this strategy
In the beginning of the summer I took a class at UChicago called 'Quantitative Portfolio Management and Algorithmic Trading'. In the beginning of the class we learned about the importance of diversification — not just as a general concept, but as tool we could take advantage of. If you have two stocks, one which is considered a good investment (say has a high sharpe ratio) and the other which is considered a bad investment, you can create a portfolio which performs better on a backtest than either of those portfolios can by themselves. By creating a tangency portfolio that weighs each stock based on their performance, you can allocate certain percentages of your total investment (such as 80/20, or -20/120 if you want to short a stock) that takes advantage of the fact that stocks move together/against each other in a predictable manner. Furthermore, if you want to get a certain mean return out of this portfolio with the least amount of volatility possible, you can do so by conducting a mean-variance analysis which will change the weights of each stock to match the target mean return while reducing the variance of the portfolio as much as possible.

I also learned in the beginning of this class about the investment strategy used by Harvard in the case study "The Harvard Management Company and Inflation-Protect Bonds", written by Luis M. Viceira. In this paper I learned that in 2000, Harvard analyzed how they invested their endowment by using a mean-variance analysis. This is when I first realized the full power of diversification: if the Harvard Management Company could use the same analysis that I had learned, it must be a viable solution to creating a solid portfolio. 

However, Harvard did not just put a handful of stocks into a backet, run a mean-variance analysis on those stocks, and call it a day. Instead, they grouped stocks together into commonly used sections such as Domestic Equity, Foreign Equity, and more. Thus grew multiple layers of mean-variance analysis: (at least) one layer for grouping investments together into asset classes, and a higher layer for weighing asset classes into the final portfolio. This is advantageous for a couple of different reasons:

1) Conducting a mean-variance analysis on assets that are similar to one another can help narrow in how these assets correlate with one another. For instance, two stocks that are in the same sector are typically very correlated; that's almost by definition, as if they weren't similar they wouldn't be put into the same sector. By analyzing assets that are highly correlated with one another, you can differentiate between macro-level market swings that uniformly affect assets in this sector apart from events that actually show how these assets differentiate from one another. 

2) Conducting a mean-variance analysis on a large number of assets is not a stable way of conducting mean-variance analysis. One disadvantage of the mean-variance analysis is that, without any adjustments, the analysis assumes that all of the data it is given (data like historical information about asset prices) is extremely important and bound to occur in the future. If there are n assets in a portfolio, there are around n^2 covariances that the analysis asumes are factual, and it conforms the weights of each asset under the assumption that these covariances will not change. When they do change out-of-sample, this massively impacts the performance of the portfolio as there are a large number of coefficients changing at once. Ultimately, a larger dimensionality creates larger imprecision, so reducing this by creating multiple levels of mean-variance analysis helps minimize these problems. 

I began thinking about creating this trading strategy soon after reading this paper. I wanted to figure out: How far could mean-variance analysis take me, even if I knew little about the company I would be investing in?


## How my strategy is built

First, note that my strategy isn't one strategy, but is instead a distribution of randomly generated strategies. I wanted this project less to be about manually choosing individual stocks based on their performance/brand recognition/future potential/ability for the CEO to manipulate their stock price on twitter, and more on allowing the mean-variance analysis (as well as a couple other tricks) to do the work for me. My hope when beginning this project was that it didn't entirely matter what stocks I chose, as long as I used the mean-variance analysis precisely. As such, the results of this project include confidence intervals for how well these portfolios did on average, as well as linear regressions to see if I could have chosen a good portfolio based off of simple metris such as sharpe ratios or profits. 

The portfolio works by being given from the investor a number of stocks in each GICS sector from the S&P 500, computing a mean variance analysis based off of backtester results from a given time-period (usually a year or so) to create a sector-wide tangency portfolio, running a backtester on said tangency portfolio over the same time-period, and then computing one last mean-variance analysis over each tangency portfolio to figure out how to weight each sector. 

Note that in this current iteration, I have two different ways of investing in a stock:

1) Holding the stock. Pretty simple; with x amount of cash, I try to buy as much of the stock as possible and hold it for the entire given time period. Note that this is also how I analyze how well the S&P 500 is doing — I hold SPY for the same amount of time. 

2) Using a Moving Average Convergence/Divergence indicator (MACD). I wanted to include a more technical investment strategy in part to practice what I had learned during class, but also in part because I thought it would provide interesting covariance interactions when comparing an investment that was just being held against an investment following the MACD strategy. I chose this against the Simple Moving Average indicator (SMA) because I knew the MACD weighs recent prices more than older prices while the SMA weighs each price the same, which generally meant it would catch onto quick upswings/downswings sooner than the SMA. 

I ran both investment strategies over each stock at the beginning before weighing the sector-wide tangency portfolio, and chose to use whichever strategy had the higher sharpe ratio. While I could have used the MACD strategy not just on stocks but also on the sector-wide portfolios I was creating, I chose not to do so for this iteration. 


## Breakdown of each individual strategy

I had 4 different portfolios I ran my code over, varying along the following variables:

* cash: The amount of money allocated to the portfolio as a whole. Less money means less flexibility in choosing when to invest in a stock; if I don't have enough money to purchase a share of AAPL, that could greatly impact how well the mean-variance analysis works. 

* num_symbols: The number of symbols to use in each GICS sector. As there were 11 GICS sectors, if num_symbols equals 5, for instance, then the portfolio would be invested in a total of 55 stocks in the S&P 500. If num_symbols ended up being greater than the number of stocks in a sector on the S&P 500 in total, then num_symbols for that specific sector would be capped at the total number of stocks on the S&P 500 in that sector. 

* start_date_insample: The starting date for running backtesters on sample data. Note that the data used is adjusted close prices obtained from Yahoo Finance. If Yahoo Finance didn't have full information on that stock or the stock wasn't public up until this date, then that stock would be tossed and another stock would be grabbed from the same sector. 

* end_date_insample: The ending date for running backtesters on sample data. 

* start_date_outsample: The starting date for running the portfolio on data it wasn't trained against. On all portfolios I ran this was equal to end_date_insample, as the freshest data is typically the most relevant, but it's kept as a separate variable just in case.

* end_date_outsample: The ending date for running the portfolio on data it wasn't trained against. The further this is away from start_date_outsample, the more likely the portfolio is to be out of date and thus perform worse. 

Now knowing the variables used, here are the 4 different portfolios I ran:

1) The baseline portfolio: cash=1,000,000, num_symbols=10, start_date_insample='2017-01-01', end_date_insample='2019-01-01', start_date_outsample='2019-01-01', end_date_outsample='2020-01-01'. Note that this baseline portfolio both has room to increase and decrease the number of symbols used per sector. Also note that this portfolio conveniently is before the coronavirus impacts America; I chose this as a baseline because I was afraid including the coronavirus would be such a shock to the investment strategy that it would automatically not work in that situation.
2) Next portfolio: cash=1,000,000, num_symbols=20, start_date_insample='2017-01-01', end_date_insample='2019-01-01', start_date_outsample='2019-01-01', end_date_outsample='2020-01-01'. Essentially the same as above, except the number of symbols increased to 20. My hypothesis for this portfolio was that 20 symbols would be too many for the mean-variance analysis to create a profitable portfolio, so I expected it to perform worse than the baseline portfolio.
3) Next portfolio:  cash=1,000,000, num_symbols=5, start_date_insample='2017-01-01', end_date_insample='2019-01-01', start_date_outsample='2019-01-01', end_date_outsample='2020-01-01'. Same as above except now num_symbols is 5. I also hypothesized that this would perform worse on average than the baseline portfolio because I thougth 5 symbols in each sector would not be enough to create a meaningful diversification. 
4) The last portfolio I created after running the above 3 portfolios and seeing how well each of them did (and, to the astute reader, is a foreshadow to the results section): cash=1,000,000, num_symbols=5, start_date_insample='2018-01-01', end_date_insample='2020-01-01', start_date_outsample='2020-01-01', end_date_outsample='2020-07-01'. A portfolio that runs right through the thick of the madness and volatility that is the market during the coronavirus. 


## Results

Note: A list of all results I found for each of these portfolios can be found in the README of the statistics folder.

1) The baseline portfolio 







