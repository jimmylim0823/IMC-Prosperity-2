# IMC-Prosperity-2024, Y-FoRM
[Link to Korean Version]()

## What is IMC Prosperity?
- Prosperity is 15-day long trading competition hosted by IMC Trading, including algorithmic trading and manual trading challenge.
- The virtual market is an utopian archipelago where major currency is SeaShells and products are Starfruit, Strawberries, etc.
- For algorithmic trading challenge, python file will be submitted to trade against other bots on limit order book.
- This year's theme included market making, OTC trading, basket trading and options trading, deanonymized trades.
- For manual trading challenge, puzzle on trading decision is given with some connection to math and game theory.

## Major Reference Links
- [IMC Prosperity](https://prosperity.imc.com)
- [Prosperity Wiki](https://imc-prosperity.notion.site/Prosperity-2-Wiki-fe650c0292ae4cdb94714a3f5aa74c85)
- Special thanks to [jmerle](https://github.com/jmerle) for contributing open source tools: [Visualizer](https://jmerle.github.io/imc-prosperity-2-visualizer/) and [Backtester](https://github.com/jmerle/imc-prosperity-2-backtester/tree/master).
  
---

## Results
### Final Rank: 189th overall (top 2%), 5th in Korea.

| Rank    | Overall | Manual | Algorithmic | Country |
| ------- | ------- | ------ | ----------- | ------- |
| Round 1 | 1913    | 2263   | 674         | 12      |
| Round 2 | 290     | 1397   | 292         | 6       |
| Round 3 | 279     | 971    | 280         | 6       |
| Round 4 | 212     | 794    | 199         | 5       |
| Round 5 | 189     | 576    | 177         | 5       |

| PnL     | Manual  | Algorithmic | Overall | Cumulative |
| ------- | ------- | ----------- | ------- | ---------- |
| Round 1 | 68,531  | 22,124      | 90,655  | 90,655     |
| Round 2 | 113,938 | 219,146     | 333,085 | 423,740    |
| Round 3 | 75,107  | 49,707      | 124,814 | 548,555    |
| Round 4 | 52,212  | 282,865     | 335,077 | 883,632    |
| Round 5 | 69,785  | 108,109     | 177,895 | 1,061,527  |

---

## Team Y-FoRM
We are undergraduate students from Yonsei University, with 2 industrial engineering major and 1 economics major.  
Also as the name of our team suggests, we are members of financial engineering and risk management club [Y-FoRM](https://yform.co.kr/).

- Ji Seob Lim [LinkedIn](https://www.linkedin.com/in/jimmylim0823/)
- Seong Yun Cho [LinkedIn](https://www.linkedin.com/in/seongyun0727/)
- Sang Hyeon Park [LinkedIn](https://www.linkedin.com/in/sang-hyeon-park-84612a271/)

---

## Round Summaries

### Some common consideration for all rounds
- Though we have an order book, it operates by turn (think of board games) rather than simultaneously.
- Orders are cancelled at every point in time, so re-processed to next timestamp.
- All products have different position limit, and position limit, trading volume and notional value decideds target PnL.
- If we the order potentially hits the positon limit, order will be canceled, so we should cap our order sizes properly.
- Scripts will run on AWS, and last year many team with complex algorithm had Lambda issue. (At most, linear/logistic regression)
- AWS does not guarantee class variables to be stored, but we can pass serialized data across timestamps thourgh `traderData`. 
- If Prosperity server goes down for a long enough period (happend twice), they might give additional 24hours for the round.
- The products in previous round will stay in the market, but marke regime may change. Continous tweaking of model is needed.


### Tutorial Round
We spent most of our time in tutorial understanding the mechanics of competition and structure of [algorithmic trading codes](https://imc-prosperity.notion.site/Writing-an-Algorithm-in-Python-658e233a26e24510bfccf0b1df647858). In the end, we decided to market make and take around the fair value, with stop loss considering the position limit.

**Some Observations**
- For both products, the order book mainly had two agents:
    - one very-passive market maker: large and symmetric order with price of +- 5 from mid-price (always worst bid/ask)
    - one active trader (noise or informed): undercutting the +-5 orders with smaller and asymetric size
- Position limit does do some work in inventory management against adverse selection
    - The maximum allowed order size of a side decreases as inventory piles up in such direction due to the trend.
    - We could further reduce the size of order in disadvantageous side to protect ourself from the trend.

**General Market Making Logic**
1. Update the fair value of product
1. Scratch by market taking for under or par valued orders (but not against worst bid/ask)
1. Stop loss if inventory piles over certain level (but not against worst bid/ask)
1. Market make around the fair value with maximum possible amount deducted by skew of order size determined by inventory

**Amethesis**
- The fair value is clearly 10000 and the mid-price is very stable (10000 +- 2), so we used fixed fair value of 10000.
- Apply the market making logic above directly as there is no need for update of fair value.

**Starfruit**
- Prices have trends (strong drift) and the trend may invert during the day.
- We used rolling linear regression $P_t=\beta_0+\beta_1 t$ to predict the price of next timestamp $\hat{P_{t+1}}=\hat{\beta_0}+\hat{\beta_0}(t+1)$.
- Utilizing [SOBI](https://www.cis.upenn.edu/~mkearns/projects/sobi.html) (Static Order Book Imbalance), we stored mid-vwap of order book rather than mid-price into a queue for data to regress.
- We examined various rolling window size to predict its fair value using heatmap.

### Round 1: Market Making
- Products and tasks of tutorial continued in Round 1 and we continued using market making around the fair value. We focused on optimizing the strategy with some data analytics. We also refactored our code in a more object-oriented way.
- We have `Strategy` class which is the base class for each product. Product configuration, order book features and variables related to our orders (submission, expected position, sum of buys and sells) is defined as instance variable of the class, and will be defined for each product.  
- `MarketMaking` class inherits `Strategy` with its instance variables and extra strategy configurations. We have `scratch_under_valued`, `stop_loss`, `market_make` method that implements the general market making logic above. Then `aggregate_orders` method calls all 3 order-generating methods and returns list of orders, which will be the input for `results[product]` in the `run` method of `Trader` class submitting the orders to the Prosperity system. Orders for `AMETHYSTS` is generaged by `MarketMaking` class in the `run` method.
- `LinearRegressionMM` inherits `MarketMaking` with its instance variables and extra rolling regression configurations. The only extra method is `predict_price` which performs a linear regrssion and prediction with data that is stored externally in class variable of `Trader` class, while the rolling part is implemented by queuing up to max rolling size while storing the data. Orders for `STARFRUIT` is generaged by `LinearRegressionMM` class in the `run` method.
- We made very high sharpe ratio PnL with almost 0 drawdown. The profit for both product was almost the same, and we managed to maintain profit per round for both product until end of the competition.

**Manual Trading Challege**  
Round 1 was on probability distribution and optimization, we misunderstood the problem missing the answer very badly. We had to bid to maximize our profit give the probability distribution of reserve price which basically is the willingness to sell at our bid. The size of potential from manual trading was way bigger than that of algorithmic trading, so we had a slow start and a long ladder to climb up.

### Round 2: OTC Trading
- The largest challenge for us and the entire community was to comprehend the intentionally vague specification of the product `ORCHIDS` from [Prosperity Wiki](https://imc-prosperity.notion.site/Round-2-accf8ab79fdf4ce5a558e49ecf83b122) and [Prosperity TV](https://www.youtube.com/watch?v=k4mV5XZZM-I).
- Price of `ORCHIDS`, according to wiki and TV, is affected by sunlight and humidity. However, the provided data had low explanatory power with unknown units making it even harder to understand. We tried analytical (building a function) and statistical (linear regression with 2 predictor, linear regression on the residual, etc.) methods which all turned out to be unsuccessful.
- Instead, we turned our focus on arbitrage opportunity between our exchange and another OTC trading venue in the South. We could convert (close posiition) orchids that we got from our exchange (both long and short) to Seashells in the South. The OTC market have an independent bid and ask, while it is a quote-driven market and will receive conversion of any size, for price of paying transportation fee + import/export tariff. As this is some sort of a single-dealer platform, we had infinite liquidity to close our position immediately, so we would make or take from exchange and close at OTC. `OTCArbitrage` class includes following methods:
1. We could enter our arbitrage position with `arbitrage_exchange_enter` which takes orders from exchange that provide direct arbitrage opportunity. The opportunity is scarace, and the risk is change in price for 1 timestamp before converting to seashelss in OTC. Thus we would only enter with arbitrage edge over `self.min_edge`.
1. We also made market with arbitrage-free pricing using OTC price + transaction cost and added some `self.mm_edge` for magin.
1. Finally, exit all open position at OTC to lock in our margin using `arbitrage_otc_exit`.
- This was all possible due to strong negative import tariff (subsidy), and all of our trade were executed in short direction. Our infinite liquidity in OTC solved the issue with inventory stacking up in one direction, and we were able to make huge profit in Round 2. Unfortunately, this alpha disappeared from Round 3 as import subsidy dropped, and it was impossible to undercut other orders with arbitrage-free pricing. Our team and many other team only relying on arbitrage had huge negative impact on cumulative overall PnL since this point, and we failed to find alpha using humidity/sunlight until the end of competition.

**Manual Trading Challege**  
Round 2 was about triangular arbitrage given the transition rate matrix. We used brute-force algorithm considering small size of the matrix.

### Round 3: Basket Arbitrage Trading
- `GIFT_BASKET` is an index basket equivalent of following constituents together: 4 `CHOCOLATE`, 6 `STRAWBERRIES` and a `ROSES`.
- We found out that the basket always traded over premium over NAV made of basket constituents. We calculated z-score of the basket-NAV spread.
- We tried stat arb between basket and constituent with z-score, but was not sucessful when we were only market taking.
- Basket had big spread and constituents had small spreads, so we decided to only market make basket with pricing using constituents.
- We shifted are fair value from mid-vwap of basket by adding `pricindg_shift = -demeaned_premium * scaling coefficient` where are pricing bias scaling coefficient uses quadratic sensitivity to spread z-score: `scaling_coefficient = self.alpha * abs(self.z_score) + self.beta * self.z_score ** 2`. This dynamic scaling will make `pricing_shift` approach 0 when z-score is close to 0 and give spike to the signal when z-score deviates significantly from the mean 0, when we have low alpha and high enough beta.
- Mechanics of `aggregate_basket_orders` work similary to market making. `BasketTrading` class will generate orders for only `GIFT_BASKET`.
1. Type of `self.basket` will be `Strategy` and type of `self.constituent` will be `Dict[Symbol: Strategy]`.
1. `calculate_fair_value` calculates fair value of basket using basket mid-vwap, demeaned premium and spread z-score.
1. Simmilar to Round 2, scratch, stop loss and market make basket. However, there are two difference:
   - `scratch_under_valued(mid_vwap=True)`: Scratch under/par-valued based on mid-vwap not fair value (as we already updated our fair value)
   - `aggresive_stop_loss`: Take max quantity from worst bid/ask for stop loss when inventory touched stop loss inventory level
- We had acceptable and steady profit for basket throughout competition. Nevertheless, we should have tried trading some constituents, even if market making was impossible due to small (0 or 1) spread.

**Manual Trading Challege**  
Round 3 was about game theory, where we choose few grid from a map to search for treasure. Expedition, maximum of 3, have huge marginal cost, and we will share the pie of the treasure we found on the grid with other participants. We tried to avoid crowding in most attractive options, and took one good but not best, and two so so options.

### Round 4: Option Trading
- `COCONUT` is an underlying asset and `COCONUT_COUPON` is an European call option with strike price of 10000 and time to maturity 250 days(rounds).
- Using our basic knowledge to option greeks, pricing of long-term options are mostly affected by change in volatility (besides the obvious change in underlying price).
- Considering limitation of computing power, we used analytic estimator from [Hallerbach (2004)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=567721) to calculate implied volatility. We found out that IV is highly mean-reverting intraday, so we decided to profit from vega trading based on rolling z-score of IV.
- We first tried a pyramid-style grid trading on IV mean reversion. We found out the mean-reverting signal is too weak for lower z-score, so we modified our trading style to trapezoid style where we cut off lower part of the pyramid below the threshold. Surprisingly, just all-in at lower z-score (near 1.5) signal was most profitable.
- We were delta hedging initially, and this led to constant loss. Our gamma was long and short for similar proportion of the time, but due to lower gamma of long-term option, all we had to pay was the spread and some loss by short gamma. We had to decide hedge, no-hedge, or flip the hedge. We decided to flip the hedge, which is trading underlying using IV level as a signal.
- During backtest, our algo profited moderately (30-40K) for the first two day and very lucratively (170-180K)for the third day (on par with Discord benchmark). This was due to high vol-of-vol of the third day. We hoped we would have high vol-of-of again, and thankfully we earned near 150K only trading the option. One issue was that our PnL for algo trading was missing in the first and thankfully moderators ran our algo again, resulting in near 300K profit which was our single-round best. Unfortunately, this alpha of vega trading from high vol-of-vol was weakened in the last round.

**Manual Trading Challege**  
Round 4 is similar to Round 1, but some game theory added. The probability distribution of willingness to buy is a function of average bids of all the participants. We took a conservative approach and didn't go too far away from the best answer.

### Round 5: De-anonymized Trade Data
- No new product was introduced in Round 5, but now name of the trader (both buyer and seleer) for market trades and own trades are visible.
- We plotted the mid-price and labeled the timestamp where given trader bought and sold to gain some insights on each trader's characteristic.
- We found some patterns that involves with the first character of the trader: A, R, V.
- Trader starting with A (maybe stands for Amatuer) was really bad


Due to delay of competition, All of us were so busy with our mid-term that we couldn't participate in round 5.
So we just modified some codes in previous round and submitted.


**Manual Trading Challege**  
Round 5 is news trading. Based on the most credible news source from north archipelago "Iceberg" (not Bloomberg), we have to allocate long and short position to tradable goods with gross position limit of 100%. We tried to take position on all products in order to reduce impact of few wrong answers. We got 5 correct 4 worng trades, but the profit from a single correct trade was able to offset all the losses from wrong trades.

---

## In Closing

- Among many algorithmic trading competitions, IMC Prosperity stands out due to its engaging storyline and well-designed graphics. Despite its challenges, it was an enjoyable experience throughout.
- The unexpected server downtime extended the competition by 24 hours, causing inconvenience and disrupting schedules for many participants. Nevertheless, I would like to express my gratitude to IMC for hosting such a fascinating event.
- I am deeply thankful to Jiseob for introducing me to this competition and encouraging participation. His initiative allowed us to explore market microstructures, CLOB, object-oriented programming, and algorithmic trading strategies extensively.
- My heartfelt thanks also go to Sanghyun, who did not give up despite the difficulties and took charge of manual trading and documenting our meetings, contributing significantly until the end.
- Despite overlapping with exam periods, the fact that we could conduct our Zoom meetings daily past midnight for over two hours without any complaints speaks volumes about the good team spirit and the enjoyable nature of the competition.
- If Prosperity3 is held, I definitely plan to participate again and hope that more people in Korea will also take interest and join the competition.
