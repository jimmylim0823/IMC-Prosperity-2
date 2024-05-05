# IMC-Prosperity-2024, Y-FoRM
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
1. Though we have an order book, it operates by turn (think of board games) rather than simultaneously.
1. Orders are cancelled at every point in time, so re-processed to next timestamp.
1. All products have different position limit, and position limit, trading volume and notional value decideds target PnL.
1. If we the order potentially hits the positon limit, order will be canceled, so we should cap our order sizes properly.
1. Scripts will run on AWS, and last year many team with complex algorithm had Lambda issue. (At most, linear/logistic regression)
1. AWS does not guarantee class variables to be stored, but we can pass serialized data across timestamps thourgh `traderData`. 
1. If Prosperity server goes down for a long enough period (happend twice), they might give additional 24hours for the round.
1. The products in previous round will stay in the market, but marke regime may change. Continous tweaking of model is needed.


### Tutorial Round
We spent most of our time in tutorial understanding the mechanics of competition and structure of [algorithmic trading codes](https://imc-prosperity.notion.site/Writing-an-Algorithm-in-Python-658e233a26e24510bfccf0b1df647858). In the end, we decided to market make and take around the fair value, with stop loss considering the position limit.

**Some Observations**
1. For both products, the order book mainly had two agents:
    - one very-passive market maker: large and symmetric order with price of +- 5 from mid-price (always worst bid/ask)
    - one active trader (noise or informed): undercutting the +-5 orders with smaller and asymetric size
1. Position limit does do some work in inventory management against adverse selection
    - The maximum allowed order size of a side decreases as inventory piles up in such direction due to the trend.
    - We could further reduce the size of order in disadvantageous side to protect ourself from the trend.

**General Market Making Logic**
1. Update the fair value of product
1. Scratch by market taking for under or par valued orders (but not against worst bid/ask)
1. Stop loss if inventory piles over certain level (but not against worst bid/ask)
1. Market make around the fair value with maximum possible amount deducted by skew of order size determined by inventory

 **Amethesis**
1. The fair value is clearly 10000 and the mid-price is very stable (10000 +- 2), so we used fixed fair value of 10000.
1. Apply the market making logic above directly as there is no need for update of fair value.

 **Starfruit**

1. Prices have trends (strong drift) and the trend may invert during the day.
1. We used rolling linear regression $P_t=\beta_0+\beta_1 t$ to predict the price of next timestamp $\hat{P_{t+1}}=\hat{\beta_0}+\hat{\beta_0}(t+1)$.
1. Utilizing [SOBI](https://www.cis.upenn.edu/~mkearns/projects/sobi.html) (Static Order Book Imbalance), we stored mid-vwap of order book rather than mid-price into a queue for data to regress.
1. We examined various rolling window size to predict its fair value using heatmap.

### Round 1: Market Making
- Products and tasks of tutorial continued in Round 1 and we continued using market making around the fair value. We focused on optimizing the strategy with some data analytics. We also refactored our code in a more object-oriented way.
- We have `Strategy` class which is the base class for each product. Product configuration, order book features and variables related to our orders (submission, expected position, sum of buys and sells) is defined as instance variable of the class, and will be defined for each product.  
- `MarketMaking` class inherits `Strategy` with its instance variables and extra strategy configurations. We have `scratch_under_valued`, `stop_loss`, `market_make` method that implements the general market making logic above. Then `aggregate_orders` method calls all 3 order-generating methods and returns list of orders, which will be the input for `results[product]` in the `run` method of `Trader` class submitting the orders to the Prosperity system. Orders for `AMETHYSTS` is generaged by `MarketMaking` class in the `run` method.
- `LinearRegressionMM` inherits `MarketMaking` with its instance variables and extra rolling regression configurations. The only extra method is `predict_price` which performs a linear regrssion and prediction with data that is stored externally in class variable of `Trader` class, while the rolling part is implemented by queuing up to max rolling size while storing the data. Orders for `STARFRUIT` is generaged by `LinearRegressionMM` class in the `run` method.
- We made very high sharpe ratio PnL with almost 0 drawdown. The profit for both product was almost the same, and we managed to maintain profit per round for both product until end of the competition.
- Manual trading challenge was on probability distribution and optimization, we misunderstood the problem missing the answer very badly. The size of potential from manual trading was way bigger than that of algorithmic trading, so we had a slow start and a long ladder to climb up.

### Round 2: OTC Trading
- The largest challenge for us and the entire community was to comprehend the intentionally vague specification of the product `ORCHIDS` from [Prosperity Wiki](https://imc-prosperity.notion.site/Round-2-accf8ab79fdf4ce5a558e49ecf83b122) and [Prosperity TV](https://www.youtube.com/watch?v=k4mV5XZZM-I).
- Price of `ORCHIDS`, according to wiki and TV, is affected by sunlight and humidity. However, the provided data had low explanatory power with unknown units making it even harder to understand. We tried analytical (building a function) and statistical (linear regression with 2 predictor, linear regression on the residual, etc.) methods which all turned out to be unsuccessful.
- Instead, we turned our focus on arbitrage opportunity between our exchange and another OTC trading venue in the South. We could convert (close posiition) orchids that we got from our exchange (both long and short) to Seashells in the South. The OTC market have an independent bid and ask, while it is a quote-driven market and will receive conversion of any size, for price of paying transportation fee + import/export tariff. As this is some sort of a single-dealer platform, we had infinite liquidity to close our position immediately, so we would make or take from exchange and close at OTC.
1. We could enter our arbitrage position with `arbitrage_exchange_enter` which takes orders from exchange that provide direct arbitrage opportunity. The opportunity is scarace, and the risk is change in price for 1 timestamp before converting to seashelss in OTC. Thus we would only enter with arbitrage edge over `self.min_edge`.
1. We also made market with arbitrage-free pricing using OTC price + transaction cost and added some `self.mm_edge` for magin.
1. Finally, exit all open position at OTC to lock in our margin using `arbitrage_otc_exit`.
- This was all possible due to strong negative import tariff (subsidy), and all of our trade were executed in short direction. Our infinite liquidity in OTC solved the issue with inventory stacking up in one direction, and we were able to make huge profit in Round 2. Unfortunately, this alpha disappeared from Round 3 as import subsidy dropped, and it was impossible to undercut other orders with arbitrage-free pricing. Our team and many other team only relying on arbitrage had big impact on cumulative overall PnL since this point.
- Manual trading challege was about triangular arbitrage given the transition rate matrix. We used brute-force algorithm considering small size of the matrix.

### Round 3: Basket Arbitrage Trading

Round 3 introduced the GIFT_BASKET, akin to an ETF product, accompanied by detailed data on each component's price and weight within the basket. This allowed us to calculate the Net Asset Value (NAV) of the gift basket.

By comparing the calculated NAV with the actual basket price, we determined the premium or discount at which the basket was trading. Utilizing the z-score of this premium, we calculated the expected price shift. This price shift was then added to the current market price to establish the Fair Value of the basket. Armed with this valuation, we employed a Market Making and Taking strategy similar to the previous rounds.

This round was particularly engaging as it mirrored real-world trading scenarios where ETFs do not always align perfectly in price movements with their underlying assets. The strategy not only tested our ability to quickly adapt and calculate under pressure but also allowed us to exploit these inefficiencies for potential gains.

Manual trading was about game theory.

### Round 4:  Call Option Trading (hedging delta and exposing to vega)

Round 4 was domain of call option trading, leveraging financial instruments disguised as "COCONUT" and "COCONUT_COUPON." Our strategy pivoted around a detailed application of the Black-Scholes-Merton model and focused on managing the option's Greeks, particularly delta and vega.

Delta Neutral Strategy: Aimed to maintain a delta-neutral position to hedge against price movements in the underlying asset, thereby primarily exposing our position to changes in volatility (vega).
Implied Volatility Tracking: Used a rolling z-score of implied volatility (IV) to gauge the overbought or oversold states of the options. This metric helped identify mean-reversion opportunities in the options market.
Mean-Reversion Based on IV: If the IV z-score crossed predefined thresholds, we implemented a pyramid-style trading strategy to exploit these IV extremes.
Dynamic Delta Hedging: Adjusted our positions in real-time to neutralize the delta, ensuring that our exposure to price movements was minimized while maintaining our positions to benefit from spikes in volatility.
Technical Implementation
Calculating Implied Volatility: We computed the IV using the BSM formula adapted for zero interest rates. This computation took into account the current market prices of the underlying asset and the option itself.
Z-Score for IV: A rolling calculation of the z-score for IV was implemented to dynamically assess the trading environment and adjust strategies accordingly.
Order Management: Orders were dynamically managed based on the IV's z-score and delta adjustments, allowing us to react promptly to market conditions.
Logging and Adjustments: Throughout the trading period, adjustments were logged meticulously to ensure transparency and enable post-analysis of the strategy's effectiveness.
Challenges and Adjustments
Market Sensitivity: The strategy required constant adjustment to the sensitivity parameters for the IV z-score to optimize the trading responses.
Technical Implementations: Due to the complexity of the calculations, particularly those involving the BSM derivatives and the dynamic hedging components, significant effort was put into ensuring that the computational overhead did not hinder real-time trading responses.

### Round 5: Multi-agent

- In this round, the information and characteristics of the orderer are provided (i.e. multi-agent round) `<br>`
- At this time, the use of the concept of "Market Microstructure". `<br>`
- Traditional economic theory that prices are continuous and found? Wrong `<br>`
- Prices are discontinuous and formed by market participants `<br>`

Due to delay of competition, All of us were so busy with our mid-term that we couldn't participate in round 5.
So we just modified some codes in previous round and submitted.

---

## In Closing

- Among many algorithmic trading competitions, IMC Prosperity stands out due to its engaging storyline and well-designed graphics. Despite its challenges, it was an enjoyable experience throughout.
- The unexpected server downtime extended the competition by 24 hours, causing inconvenience and disrupting schedules for many participants. Nevertheless, I would like to express my gratitude to IMC for hosting such a fascinating event.
- I am deeply thankful to Jiseob for introducing me to this competition and encouraging participation. His initiative allowed us to explore market microstructures, CLOB, object-oriented programming, and algorithmic trading strategies extensively.
- My heartfelt thanks also go to Sanghyun, who did not give up despite the difficulties and took charge of manual trading and documenting our meetings, contributing significantly until the end.
- Despite overlapping with exam periods, the fact that we could conduct our Zoom meetings daily past midnight for over two hours without any complaints speaks volumes about the good team spirit and the enjoyable nature of the competition.
- If Prosperity3 is held, I definitely plan to participate again and hope that more people in Korea will also take interest and join the competition.
