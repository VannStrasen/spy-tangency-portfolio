# spy-tangency-portfolio
Randomized portfolio builder I made over the summer of 2020.

The key takeaway from this project is that building a tangency portfolio out of historical stock data can (on average) create a profitable portfolio, even if you don't know anything in-depth about the sector/company you're investing in.

## Inspiration for this strategy
In the beginning of the summer I took a class at UChicago called 'Quantitative Portfolio Management and Algorithmic Trading'. In the beginning of the class we learned about the importance of diversification — not just as a general concept, but as tool we could take advantage of. If you have two stocks, one which is considered a good investment (say has a high sharpe ratio) and the other which is considered a bad investment, you can create a portfolio which performs better on a backtest than either of those portfolios can by themselves. By creating a tangency portfolio that weighs each stock based on their performance, you can allocate certain percentages of your total investment (such as 80/20, or -20/120 if you want to short a stock) that takes advantage of the fact that stocks move together/against each other in a predictable manner. Furthermore, if you want to get a certain mean return out of this portfolio with the least amount of volatility possible, you can do so by conducting a mean-variance analysis which will change the weights of each stock to match the target mean return while reducing the variance of the portfolio as much as possible.

I also learned in the beginning of this class about the investment strategy used by Harvard in the case study "The Harvard Management Company and Inflation-Protect Bonds", written by Luis M. Viceira. In this paper I learned that in 2000, Harvard analyzed how they invested their endowment by using a mean-variance analysis. This is when I first realized the full power of diversification: if the Harvard Management Company could use the same analysis that I had learned, it must be a viable solution to creating a solid portfolio. 

However, Harvard did not just put a handful of stocks into a backet, run a mean-variance analysis on those stocks, and call it a day. Instead, they grouped stocks together into commonly used sections such as Domestic Equity, Foreign Equity, and more. Thus grew multiple layers of mean-variance analysis: (at least) one layer for grouping investments together into asset classes, and a higher layer for weighing asset classes into the final portfolio. This helped solve two different problems:

\1) if you conduct a mean-variance analysis on a large group of investments, 


## How my strategy is built


## Results
